import os
import tracemalloc
import time
from sys import getsizeof
import pickle
import json
import requests

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

# get nr of instances
n_instances = new_pc.config['N_INSTANCES']
print("Simulation: N_INSTANCES to simulate: " +  str(n_instances))

new_window = DataWindow()
MIN_DATA_POINTS = 5

# rpy2 r objects access
r = robjects.r
# source R file of cognition implementation
r.source('L3_PC_Simulation.R')
# r data.frame to pandas conversion 
pandas2ri.activate()

for msg in new_pc.consumer:

    new_data = new_pc.decode_avro_msg(msg)
    new_data_point = new_window.Data_Point(new_data['id'], new_data['x'], new_data['y'])
    new_window.append_and_check(new_data_point)

    if len(new_window.data) < MIN_DATA_POINTS:
        print(f"Collecting training data for Test function generator "
              f"({len(new_window.data)}/{MIN_DATA_POINTS})")
    else:
        # take x/y to instantiate R simulator with nr_instances
        generateTestFunctions = robjects.r["generateTestFunctions"]

        df = new_window.to_df()

        testSet = generateTestFunctions(df, n_instances)

        objective_pickle = pickle.dumps(testSet)

        simulation_data = {'id': new_data['id'],
                      'simulation': objective_pickle
                      }

        new_pc.send_msg(simulation_data)
