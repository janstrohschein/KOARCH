import os
from scipy.optimize import differential_evolution
from math import ceil
import pickle
import numpy as np

from classes.KafkaPC import KafkaPC
# from Use_Cases.VPS_Popcorn_Production.Kubernetes.src.classes import KafkaPC


class Optimizer(KafkaPC):
    def __init__(self, config_path, config_section):
        super().__init__(config_path, config_section)

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
        Outgoing Avro Message:
        "name": "Model_Application",
        "fields": [
            {"name": "phase", "type": ["enum"], "symbols": ["init", "observation"]},
            {"name": "model_name", "type": ["string"]},
            {"name": "id_x", "type": ["int"]},
            {"name": "n_data_points", "type": ["int"]},
            {"name": "id_start_x", "type": ["int"]},
            {"name": "model_size", "type": ["int"]},
            {"name": "x", "type": ["float"]},
            {"name": "pred_y", "type": ["float"]},
            {"name": "rmse", "type": ["null, float"]},
            {"name": "mae", "type": ["null, float"]},
            {"name": "rsquared", "type": ["null, float"]},
            {"name": "CPU_ms", "type": ["int"]},
            {"name": "RAM", "type": ["int"]}
        ]
        """
        appl_result = {"phase": "observation",
                       "model_name": "test",
                       "id_x": 123,
                       "n_data_points": 123,
                       "id_start_x": 9,
                       "model_size": 12,
                       "x": x,
                       "pred_y": 2.3,
                       "CPU_ms": 1,
                       "RAM": 2}

        print(f"sending from apply_to_cpps() with x={x}")
        self.send_msg(topic="AB_application_results", data=appl_result)
        for msg in self.consumer:
            new_msg = self.decode_avro_msg(msg)
            print("Result arrived in apply_to_cpps")
            print(new_msg)

            # get y from returning message
            y = "something"
        return y

    def objective_function(self, x):
        pass
        # TODO implement objective function

    def process_test_function(self, msg):
        new_test_function = self.decode_avro_msg(msg)

        # TODO instantiate different optimizers
        result = differential_evolution(self.objective_function,
                                        self.bounds,
                                        maxiter=self.N_MAX_ITER,
                                        popsize=self.N_POP_SIZE)

        # fill dictionary with required result fields
        simulation_results = {"field_name1": 3,
                              "field_name2": 2}

        self.send_msg(topic="AB_simulation_results", data=simulation_results)

    def process_production_data(self):

        new_production_data = self.decode_avro_msg(msg)

        # get x from production data
        # TODO instantiate different optimizers
        result = differential_evolution(self.apply_on_cpps,
                                        self.bounds,
                                        maxiter=self.N_MAX_ITER,
                                        popsize=self.N_POP_SIZE)

        # fill dictionary with required result fields
        application_results = {"field_name1": 3,
                               "field_name2": 2}

        self.send_msg(topic="AB_application_results", data=application_results)


env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}


"""
def evaluate_diff_evo(x):
    X = np.array(x).reshape(-1, 1)
    res = model.predict(X)

    return res[0].item()
"""


new_pc = Optimizer(**env_vars)

for msg in new_pc.consumer:
    new_pc.func_dict[msg.topic](msg)
