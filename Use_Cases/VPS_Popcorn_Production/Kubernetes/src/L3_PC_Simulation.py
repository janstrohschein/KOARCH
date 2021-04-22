import os
import tracemalloc
import time
from sys import getsizeof
import pickle
import json
import requests
import numpy as np

import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

from classes.KafkaPC import KafkaPC
from classes.caai_util import ModelLearner, DataWindow, get_cv_scores
import sys
import warnings

if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

new_pc = KafkaPC(**env_vars)

new_window = DataWindow()
MIN_DATA_POINTS = 5

X_MIN = 4000
X_MAX = 10100
BUDGET = 40
N_INSTANCES = new_pc.config['N_INSTANCES']
print("Simulation: N_INSTANCES to simulate: " +  str(N_INSTANCES))


# rpy2 r objects access
r = robjects.r
# source R file of cognition implementation
r.source('L3_PC_Simulation.R')
# r data.frame to pandas conversion 
pandas2ri.activate()

for msg in new_pc.consumer:

    """
    Incoming AVRO Message:
    {"type": "record",
    "name": "Simulation_Data",
    "fields": [
        {"name": "id", "type": ["int"]},
        {"name": "new_simulation", "type": ["bool"]},
        {"name": "x", "type": ["float"]},
        {"name": "y", "type": ["float"]}
        ]
        }
    """
    new_data = new_pc.decode_avro_msg(msg)
    new_data_point = new_window.Data_Point(new_data['id'], new_data['x'], new_data['y'])
    new_window.append_and_check(new_data_point)

    if len(new_window.data) < MIN_DATA_POINTS:
        print(f"Collecting training data for Test function generator "
              f"({len(new_window.data)}/{MIN_DATA_POINTS})")
    else:
        # TODO consider theta, etha, count iteration
        # take x/y to instantiate R simulator with nr_instances
        generateTestFunctions = robjects.r["generateTestFunctions"]

        df = new_window.to_df()

        testInstance = generateTestFunctions(df, N_INSTANCES)
        # TODO compute baseline performance results and send to cognition?
        selection_phase = 1
        repetition = 1
        CPU_ms = 0.1
        RAM = 0.05
        samples = np.random.uniform(low=X_MIN, high=X_MAX, size=BUDGET)
        y = testInstance(samples)
        best_y = min(y)
        best_id = np.argmin(y)
        best_x = samples[best_id]
        
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
        simulation_result_data = {
            "selection_phase": selection_phase,
            "algorithm": "baseline",
            "repetition": repetition,
            "budget": BUDGET,
            "x": best_x,
            "y": best_y,
            "CPU_ms": CPU_ms,
            "RAM": RAM,
        }
        new_pc.send_msg(topic='AB_simulation_results', data=simulation_result_data)

        objective_pickle = pickle.dumps(testInstance)
        simulation_data = {'id': new_data['id'],
                      'simulation': objective_pickle
                      }

        new_pc.send_msg(topic='AB_test_function', data=simulation_data)
