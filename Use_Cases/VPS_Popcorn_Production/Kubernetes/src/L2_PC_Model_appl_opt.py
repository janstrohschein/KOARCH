import os
from scipy.optimize import differential_evolution
from math import ceil
import pickle
import numpy as np

from classes.KafkaPC import KafkaPC

class ModelOptimizer(KafkaPC):
    def __init__(self, config_path, config_section):
        super().__init__(config_path, config_section)

        self.func_dict = {"AB_simulation_model_data": self.process_test_function,
                          "AB_model_data": self.process_raw_data}

    def process_test_function(self, msg):
        """
        "name": "Simulation_Model",
        "fields": [
            {"name": "selection_phase", "type": ["int"]},
            {"name": "algorithm", "type": ["string"]},
            {"name": "repetition", "type": ["int"]},
            {"name": "budget", "type": ["int"]},
            {"name": "model", "type": ["bytes"]},
            {"name": "CPU_ms", "type": ["float"]},
            {"name": "RAM", "type": ["float"]}
            ]
        """
        new_model = new_pc.decode_avro_msg(msg)

        self.model = pickle.loads(new_model['model'])
        result = differential_evolution(self.evaluate_diff_evo, bounds, maxiter=N_MAX_ITER, popsize=N_POP_SIZE)

        surrogate_x = result.x[0]
        surrogate_y = result.fun

        print(f"The {new_model['algorithm']} optimization suggests "
            f"x={round(surrogate_x, 3)}, y={round(surrogate_y, 3)}")

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
        
        sim_result_data = {'selection_phase': new_model['selection_phase'],
                        'algorithm': new_model['algorithm'],
                        'repetition': new_model['repetition'],
                        'budget': new_model['budget'],
                        'x': surrogate_x,
                        'y': surrogate_y,
                        'CPU_ms': new_model['CPU_ms'],
                        'RAM': new_model['RAM']
                        }

        new_pc.send_msg(topic='AB_simulation_results', data=sim_result_data)

    def process_raw_data(self, msg):
        """
        "name": "Model",
        "fields": [
            {"name": "phase", "type": ["enum"], "symbols": ["init", "observation"]},
            {"name": "model_name", "type": ["string"]},
            {"name": "n_data_points", "type": ["int"]},
            {"name": "id_start_x", "type": ["int"]},
            {"name": "model", "type": ["bytes"]},
            {"name": "model_size", "type": ["int"]},
            {"name": "rmse", "type": ["null", "float"]},
            {"name": "mae", "type": ["null", "float"]},
            {"name": "rsquared", "type": ["null", "float"]},
            {"name": "CPU_ms", "type": ["int"]},
            {"name": "RAM", "type": ["int"]}
            ]
        """

        new_model = new_pc.decode_avro_msg(msg)

        self.model = pickle.loads(new_model['model'])
        result = differential_evolution(self.evaluate_diff_evo, bounds, maxiter=N_MAX_ITER, popsize=N_POP_SIZE)

        surrogate_x = result.x[0]
        surrogate_y = result.fun

        print(f"The {new_model['model_name']} optimization suggests "
            f"x={round(surrogate_x, 3)}, y={round(surrogate_y, 3)}")

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
        model_appl_data = {'phase': new_model['phase'],
                        'algorithm': new_model['model_name'],
                        'id': new_model['id'],
                        'x': surrogate_x,
                        'y': surrogate_y
                        }

        new_pc.send_msg(topic='AB_application_results', data=model_appl_data)
    
    def evaluate_diff_evo(self, x):
        X = np.array(x).reshape(-1, 1)
        res = self.model.predict(X)

        return res[0].item()

env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

# configuration constants
N_INITIAL_DESIGN = 5
N_OPTIMIZATION_BUDGET = 200
N_POP_SIZE = 20
N_MAX_ITER = ceil(N_OPTIMIZATION_BUDGET / N_POP_SIZE)

X_MIN = 4000
X_MAX = 10100

bounds = [(X_MIN, X_MAX)]

new_pc = ModelOptimizer(**env_vars)

for msg in new_pc.consumer:
    new_pc.func_dict[msg.topic](msg)