import os
import tracemalloc
import time
from sys import getsizeof
import pickle
import json
import requests

from classes.KafkaPC import KafkaPC
from classes.caai_util import ModelLearner, DataWindow, get_cv_scores
import sys
import warnings

if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"


def get_model_parameters(API_URL):

    ENDPOINT_USE_CASE = "/use_case/"
    URL = API_URL + ENDPOINT_USE_CASE
    api_request = requests.get(url=URL)
    use_case_info = json.loads(api_request.content)

    payload = {"use_case": use_case_info['use_case'],
               "goal": use_case_info['goal'],
               "feature": use_case_info['feature'],
               "algorithm": MODEL_ALGORITHM}

    ENDPOINT_KNOWLEDGE = "/knowledge/algorithm/"
    URL = API_URL + ENDPOINT_KNOWLEDGE
    api_request = requests.get(url=URL, params=payload)
    algo_info = json.loads(api_request.content)

    MODEL_PARAMETERS = {}

    for key, value in algo_info["parameter"].items():
        if type(value) is str:
            MODEL_PARAMETERS[key] = value
        elif type(value) is dict:
            MODEL_PARAMETERS[key] = value['default']

    return MODEL_PARAMETERS


env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

"""
env_vars = {'in_topic': {'DB_raw_data': './schema/data.avsc'},
            'in_group': 'kriging',
            'in_schema_file': './schema/data.avsc',
            'out_topic': 'AB_model_data',
            'out_schema_file': './schema/model.avsc'}
"""

new_pc = KafkaPC(**env_vars)

MODEL_ALGORITHM = new_pc.config['MODEL_ALGORITHM']

API_URL = new_pc.config['API_URL']
MODEL_PARAMETERS = get_model_parameters(API_URL)

new_window = DataWindow()
MIN_DATA_POINTS = 5

for msg in new_pc.consumer:
    """
    "name": "Data",
    "fields": [
        {"name": "phase", "type": ["string"]},
        {"name": "id_x", "type": ["int"]},
        {"name": "x", "type": ["float"]},
        {"name": "y", "type": ["float"]}
        ]
    """
    new_data = new_pc.decode_avro_msg(msg)

    new_data_point = new_window.Data_Point(new_data['id'], new_data['x'], new_data['y'])
    new_window.append_and_check(new_data_point)

    if len(new_window.data) < MIN_DATA_POINTS:
        print(f"Collecting training data for {MODEL_ALGORITHM} "
              f"({len(new_window.data)}/{MIN_DATA_POINTS})")
    else:
        # performance tracking
        tracemalloc.start()
        start = time.perf_counter()
        start_process = time.process_time()

        ML = ModelLearner(MODEL_ALGORITHM, MODEL_PARAMETERS)

        X, y = new_window.get_arrays(reshape_x=ML.reshape_x, reshape_y=ML.reshape_y)
        id_start_x = new_window.get_id_start_x()
        ML.model.fit(X, y)

        # print(f'n = {len(X)}')
        rmse_score, mae_score, r2_score = get_cv_scores(ML.model, X, y)
        print(f"Update model with (x={round(new_data['x'], 3)}, y={round(new_data['y'], 3)}) -> "
              f"RMSE: {round(rmse_score, 3)}")

        real_time = round(time.perf_counter() - start, 4)
        process_time = round(time.process_time() - start_process, 4)

        # print(f'Found result in {real_time}s')
        # print(f'CPU time is {process_time}s')

        current, peak = tracemalloc.get_traced_memory()
        current_mb = current / 10 ** 6
        peak_mb = peak / 10 ** 6

        # print(f"Current memory usage is {current_mb}MB; Peak was {peak_mb}MB")
        tracemalloc.stop()

        model_pickle = pickle.dumps(ML.model)

        """
        "name": "Model",
        "fields": [
            {"name": "phase", "type": ["enum"], "symbols": ["init", "observation"]},
            {"name": "model_name", "type": ["string"]},
            {"name": "n_data_points", "type": ["int"]},
            {"name": "id_start_x", "type": ["int"]},
            {"name": "model", "type": ["bytes"]},
            {"name": "model_size", "type": ["int"]},
            {"name": "rmse", "type": ["null, float"]},
            {"name": "mae", "type": ["null, float"]},
            {"name": "rsquared", "type": ["null, float"]},
            {"name": "CPU_ms", "type": ["float"]},
            {"name": "RAM", "type": ["float"]}
            ]
        """

        model_data = {'phase': new_data['phase'],
                      'model_name': MODEL_ALGORITHM,
                      'id': new_data['id'],
                      'n_data_points': len(X),
                      'id_start_x': id_start_x,
                      'model': model_pickle,
                      'model_size': getsizeof(model_pickle),
                      'rmse': rmse_score,
                      'mae': mae_score,
                      'rsquared': r2_score,
                      'CPU_ms': real_time,
                      'RAM': peak_mb
                      }

        new_pc.send_msg(model_data)
