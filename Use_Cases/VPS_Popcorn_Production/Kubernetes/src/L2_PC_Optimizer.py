import os
from scipy.optimize import differential_evolution
from math import ceil
import pickle
import numpy as np

import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

from classes.KafkaPC import KafkaPC
# from Use_Cases.VPS_Popcorn_Production.Kubernetes.src.classes import KafkaPC

pandas2ri.activate()

class Optimizer(KafkaPC):
    def __init__(self, config_path, config_section):
        super().__init__(config_path, config_section)
        self.optimizer_name = 'Differential evolution'
        self.raw_data_dict = {}
        self.last_raw_id = None
        self.func_dict = {
            "AB_test_function": self.process_test_function,
            "DB_raw_data": self.process_production_data,
        }
        # configuration constants
        self.N_INITIAL_DESIGN = 5
        self.N_OPTIMIZATION_BUDGET = 200
        self.N_POP_SIZE = 20
        self.N_MAX_ITER = ceil(self.N_OPTIMIZATION_BUDGET / self.N_POP_SIZE)

        self.X_MIN = 4000
        self.X_MAX = 10100

        self.bounds = [(self.X_MIN, self.X_MAX)]

    def apply_on_cpps(self, x):
        """
        "name": "New_X",
        "fields": [
            {"name": "new_x", "type": ["float"]}
            ]
        """
        apply_on_cpps_dict = {'algorithm': self.optimizer_name, 'new_x': x[0] }

        print(f"sending from apply_to_cpps() with x={x[0]}")
        self.send_msg(topic="AB_apply_on_cpps", data=apply_on_cpps_dict)
        for msg in self.consumer:
            print(f"Arrived on topic: {msg.topic} ")
            if msg.topic == 'AB_raw_data':
                new_msg = self.decode_avro_msg(msg)
                # get y from returning message
                return new_msg['y']

    def process_test_function(self, msg):
        print("Process test instance from Simulation on AB_test_function")
        """
        "name": "Simulation",
        "fields": [
            {"name": "id", "type": ["int"]},
            {"name": "simulation", "type": ["byte"]},
            ]
        """
        new_test_function = self.decode_avro_msg(msg)
        objFunction = pickle.loads(new_test_function['simulation'])

        # TODO instantiate different optimizers
        result = differential_evolution(objFunction,
                                        self.bounds,
                                        maxiter=self.N_MAX_ITER,
                                        popsize=self.N_POP_SIZE)
        best_x = result.x[0]
        best_y = None
        if isinstance(result.fun, np.float64):
            best_y = result.fun
        else:
            best_y = result.fun[0]
        algorithm = self.optimizer_name
        repetition = 1
        selection_phase = 1
        budget = (self.N_MAX_ITER * self.N_POP_SIZE) + self.N_POP_SIZE
        # TODO 
        CPU_ms = 0.35
        RAM = 23.6

        """
         "name": "Simulation_Result",
        "fields": [
            {"name": "selection_phase", "type": ["int"]},
            {"name": "algorithm", "type": ["string"]},
            {"name": "repetition", "type": ["int"]},
            {"name": "budget", "type": ["int"]},
            {"name": "x", "type": ["float"]},
            {"name": "y", "type": ["float"]},
            {"name": "CPU_ms", "type": ["float"]},
            {"name": "RAM", "type": ["float"]}
            ]
        """
        # fill dictionary with required result fields
        simulation_result = {"algorithm": algorithm,
                              "selection_phase": selection_phase,
                              "repetition": repetition,
                              "budget": budget,  
                              "CPU_ms": CPU_ms,
                              "RAM": RAM, 
                              "x": best_x,
                              "y": best_y                            
                              }

        self.send_msg(topic="AB_simulation_results", data=simulation_result)

    def process_production_data(self, msg):
        new_production_data = self.decode_avro_msg(msg)
        if(new_production_data['algorithm'] == OPTIMIZER_NAME):
            print("Process production data from Monitoring on DB_raw_data")
            id = new_production_data['id']
            self.last_raw_id = id
            self.raw_data_dict[id] = {
                'id': new_production_data['id'],
                'phase': new_production_data['phase'],
                'algorithm': OPTIMIZER_NAME,
                'x': new_production_data['x'],
    #            'y': new_production_data['y']
            }
            if new_production_data['phase'] == 'init':
                print("Production still in init phase")
                return
            
            

            # get x,y from production data
            # TODO instantiate different optimizers
            result = differential_evolution(self.apply_on_cpps,
                                            self.bounds,
                                            maxiter=self.N_MAX_ITER,
                                            popsize=self.N_POP_SIZE)
            x = result.x[0]
            y = result.fun

            """
            "name": "Application_Result",
            "fields": [
                {"name": "phase", "type": ["string"]},
                {"name": "algorithm", "type": ["string"]},
                {"name": "id", "type": ["int"]},
                {"name": "x", "type": ["float"]},
                {"name": "y", "type": ["float"]}
                ]
            """
            # fill dictionary with required result fields
            application_results = {'phase': new_production_data['phase'],
                            'algorithm': OPTIMIZER_NAME,
                            'id': new_production_data['id'],
                            'x': x,
                            'y': y
                            }

            self.send_msg(topic="AB_application_results", data=application_results)


env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}


OPTIMIZER_NAME = "Differential Evolution"

"""
def evaluate_diff_evo(x):
    X = np.array(x).reshape(-1, 1)
    res = model.predict(X)

    return res[0].item()
"""


new_pc = Optimizer(**env_vars)

for msg in new_pc.consumer:
    new_pc.func_dict[msg.topic](msg)
