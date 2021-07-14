import warnings
import sys
import os
import tracemalloc
import time
from sys import getsizeof, exit
import pickle
import json
import requests

from rpy2.robjects import pandas2ri

import numpy as np

from Big_Data_Platform.Kubernetes.Kafka_Client.Confluent_Kafka_Python.src.classes.CKafkaPC import KafkaPC

from Use_Cases.VPS_Popcorn_Production.Kubernetes.src.classes.caai_util import ModelLearner, DataWindow, get_cv_scores


if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

X_MIN = 4000
X_MAX = 10100
N_INITIAL_DESIGN = 5

pandas2ri.activate()


class Learner(KafkaPC):
    def __init__(self, config_path, config_section):
        super().__init__(config_path, config_section)

        self.func_dict = {
            "AB_test_function": self.process_test_function,
            "DB_features": self.process_features,
        }

    def get_model_parameters(self, API_URL):

        ENDPOINT_USE_CASE = "/use_case/"
        URL = API_URL + ENDPOINT_USE_CASE
        api_request = requests.get(url=URL)
        use_case_info = json.loads(api_request.content)

        payload = {
            "use_case": use_case_info["use_case"],
            "goal": use_case_info["goal"],
            "feature": use_case_info["feature"],
            "algorithm": MODEL_ALGORITHM,
        }

        ENDPOINT_KNOWLEDGE = "/knowledge/algorithm/"
        URL = API_URL + ENDPOINT_KNOWLEDGE
        api_request = requests.get(url=URL, params=payload)
        algo_info = json.loads(api_request.content)

        MODEL_PARAMETERS = {}

        for key, value in algo_info["parameter"].items():
            if type(value) is str:
                MODEL_PARAMETERS[key] = value
            elif type(value) is dict:
                MODEL_PARAMETERS[key] = value["default"]

        return MODEL_PARAMETERS

    def process_test_function(self, msg):
        """
        "name": "Simulation",
        "fields": [
            {"name": "id", "type": ["int"]},
            {"name": "selection_phase", "type": ["int"]},
            {"name": "simulation", "type": ["byte"]},
            ]
        """
        # new_sim = self.decode_avro_msg(msg)
        new_sim = self.decode_msg(msg)
        # extract objective
        objFunction = pickle.loads(new_sim["simulation"])
        selection_phase = new_sim["selection_phase"]

        # performance tracking
        tracemalloc.start()
        start = time.perf_counter()
        start_process = time.process_time()

        budget = 20
        # initdesign to sample obj for initial model training
        X = np.linspace(X_MIN, X_MAX, num=budget)
        # evaluate design
        y = objFunction(X)
        # fit model
        ML = ModelLearner(MODEL_ALGORITHM, MODEL_PARAMETERS)

        if ML.reshape_x:
            X = X.reshape(-1, 1)

        if ML.reshape_y:
            y = y.reshape(-1, 1)
        ML.model.fit(X, y)

        rmse_score, mae_score, r2_score = get_cv_scores(ML.model, X, y)
        print(
            f"Fitted model of test instance with  -> " f"RMSE: {round(rmse_score, 3)}"
        )

        real_time = round(time.perf_counter() - start, 4)
        process_time = round(time.process_time() - start_process, 4)

        # print(f'Found result in {real_time}s')
        # print(f'CPU time is {process_time}s')

        current, peak = tracemalloc.get_traced_memory()
        current_mb = current / 10 ** 6
        peak_mb = peak / 10 ** 6

        # print(f"Current memory usage is {current_mb}MB; Peak was {peak_mb}MB")
        tracemalloc.stop()

        # pickle model and send to optimizer
        model_pickle = pickle.dumps(ML.model)

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

        simulation_model_data = {
            "selection_phase": selection_phase,
            "algorithm": MODEL_ALGORITHM,
            "repetition": 1,
            "budget": budget,
            "model": model_pickle,
            "CPU_ms": real_time,
            "RAM": peak_mb,
        }

        self.send_msg(topic="AB_simulation_model_data",
                      message=simulation_model_data)
        exit(0)

    def process_features(self, msg):
        """
        "name": "Data",
        "fields": [
            {"name": "phase", "type": ["string"]},
            {"name": "algorithm", "type": ["string"]},
            {"name": "id_x", "type": ["int"]},
            {"name": "x", "type": ["float"]},
            {"name": "y", "type": ["float"]}
            ]


        new_data_point = {
            "cycle": current_data_point,
            "timestamp": 12345,
            "x": {"x": new_x},
            "y_values": {"y": new_y},
            "y_agg": new_y,
            "y_values_norm": {"y": new_y},
            "y_agg_norm": new_y
        }


        """
        new_data = self.decode_msg(msg)
        # print(new_data)

        new_data_point = new_window.Data_Point(
            new_data["cycle"], new_data["x"]["x"], new_data["y_agg_norm"]
        )
        new_window.append_and_check(new_data_point)

        if len(new_window.data) < MIN_DATA_POINTS:
            print(
                f"Collecting training data for {MODEL_ALGORITHM} "
                f"({len(new_window.data)}/{MIN_DATA_POINTS})"
            )
        # elif new_data["algorithm"] == MODEL_ALGORITHM:
        else:
            # performance tracking
            tracemalloc.start()
            start = time.perf_counter()
            start_process = time.process_time()

            ML = ModelLearner(MODEL_ALGORITHM, MODEL_PARAMETERS)

            X, y = new_window.get_arrays(
                reshape_x=ML.reshape_x, reshape_y=ML.reshape_y)
            id_start_x = new_window.get_id_start_x()
            ML.model.fit(X, y)

            # print(f'n = {len(X)}')
            rmse_score, mae_score, r2_score = get_cv_scores(ML.model, X, y)
            print(
                f"Update model with (x={round(new_data['x']['x'], 3)}, y={round(new_data['y_agg_norm'], 3)}) -> "
                f"RMSE: {round(rmse_score, 3)}"
            )

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

            model_data = {
                "phase": "observation",
                "model_name": MODEL_ALGORITHM,
                "id": new_data["cycle"],
                "n_data_points": len(X),
                "id_start_x": id_start_x,
                "model": model_pickle,
                "model_size": getsizeof(model_pickle),
                "rmse": rmse_score,
                "mae": mae_score,
                "rsquared": r2_score,
                "CPU_ms": real_time,
                "RAM": peak_mb,
            }

            self.send_msg(topic="AB_model_data", message=model_data)


env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}


new_pc = Learner(**env_vars)

MODEL_ALGORITHM = new_pc.config["MODEL_ALGORITHM"]

API_URL = new_pc.config["API_URL"]
MODEL_PARAMETERS = new_pc.get_model_parameters(API_URL)

new_window = DataWindow()
MIN_DATA_POINTS = 5

try:
    while True:
        msg = new_pc.consumer.poll(0.1)

        if msg is None:
            continue

        elif msg.error() is not None:
            print(f"Error occured: {str(msg.error())}")

        else:
            new_pc.func_dict[msg.topic()](msg)

except KeyboardInterrupt:
    pass

finally:
    new_pc.consumer.close()
