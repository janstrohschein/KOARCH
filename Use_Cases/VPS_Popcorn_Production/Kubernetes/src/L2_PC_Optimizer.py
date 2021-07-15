import os
from sys import exit

import pickle
import numpy as np
import json
import requests

import random

from rpy2.robjects import pandas2ri

from Use_Cases.VPS_Popcorn_Production.Kubernetes.src.classes.caai_util import OptAlgorithm
from Big_Data_Platform.Kubernetes.Kafka_Client.Confluent_Kafka_Python.src.classes.CKafkaPC import KafkaPC


pandas2ri.activate()


class Optimizer(KafkaPC):
    def __init__(self, config_path, config_section):
        super().__init__(config_path, config_section)
        self.X_MIN = 4000
        self.X_MAX = 10100
        self.bounds = [(self.X_MIN, self.X_MAX)]
        self.raw_data_dict = {}
        self.last_raw_id = None
        self.func_dict = {
            "AB_test_function": self.process_test_function,
            "DB_features": self.process_features,
        }

    def get_optimizer_parameters(self, API_URL):
        ENDPOINT_USE_CASE = "/use_case/"
        URL = API_URL + ENDPOINT_USE_CASE
        api_request = requests.get(url=URL)
        use_case_info = json.loads(api_request.content)

        payload = {
            "use_case": use_case_info["use_case"],
            "goal": use_case_info["goal"],
            "feature": use_case_info["feature"],
            "algorithm": OPTIMIZER_NAME,
        }

        ENDPOINT_KNOWLEDGE = "/knowledge/algorithm/"
        URL = API_URL + ENDPOINT_KNOWLEDGE
        api_request = requests.get(url=URL, params=payload)
        algo_info = json.loads(api_request.content)

        OPTIMIZER_PARAMETERS = {}

        for key, value in algo_info["parameter"].items():
            if type(value) is str:
                OPTIMIZER_PARAMETERS[key] = value
            elif type(value) is dict:
                OPTIMIZER_PARAMETERS[key] = value["default"]

        return OPTIMIZER_PARAMETERS

    def apply_on_cpps(self, x):
        """
        "name": "New_X",
        "fields": [
            {"name": "new_x", "type": ["float"]}
            ]
        """
        apply_on_cpps_dict = {"algorithm": OPTIMIZER_NAME, "new_x": x[0]}

        print(f"sending from apply_to_cpps() with x={x[0]}")
        self.send_msg(topic="AB_apply_on_cpps", message=apply_on_cpps_dict)

        try:
            while True:
                msg = new_pc.consumer.poll(0.1)

                if msg is None:
                    continue

                elif msg.error() is not None:
                    print(f"Error occured: {str(msg.error())}")

                else:
                    print(f"Arrived on topic: {msg.topic()} ")
                    if msg.topic() == "AB_raw_data":
                        new_msg = self.decode_msg(msg)
                        # get y from returning message
                        return new_msg["y"]

        except KeyboardInterrupt:
            pass

    def process_test_function(self, msg):
        print("Process test instance from Simulation on AB_test_function")
        print("Optimizer: " + OPTIMIZER_NAME)
        """
        "name": "Simulation",
        "fields": [
            {"name": "id", "type": ["int"]},
            {"name": "selection_phase", "type": ["int"]},
            {"name": "simulation", "type": ["byte"]},
            ]
        """
        new_test_function = self.decode_msg(msg)
        objFunction = pickle.loads(new_test_function["simulation"])
        selection_phase = new_test_function["selection_phase"]

        # instantiate optimizer
        alg = OptAlgorithm(self.bounds, OPTIMIZER_NAME, OPTIMIZER_PARAMETERS)
        result = alg.run(objFunction)
        best_x = result.x[0]
        best_y = None
        if isinstance(result.fun, np.float64):
            best_y = result.fun
        else:
            best_y = result.fun[0]
        algorithm = OPTIMIZER_NAME

        budget = result.nfev
        # QUESTION include real resource consumption in Cognition?
        repetition = 1

        CPU_ms = 0.35 + random.uniform(0, 1)
        RAM = 23.6 + random.uniform(0, 1)

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
        simulation_result = {
            "algorithm": algorithm,
            "selection_phase": selection_phase,
            "repetition": repetition,
            "budget": budget,
            "CPU_ms": CPU_ms,
            "RAM": RAM,
            "x": best_x,
            "y": best_y,
        }

        self.send_msg(topic="AB_simulation_results", message=simulation_result)
        exit(0)

    def process_features(self, msg):
        new_production_data = self.decode_msg(msg)
        # if new_production_data["algorithm"] == OPTIMIZER_NAME:
        print("Process production data from Monitoring on DB_features")
        id = new_production_data["cycle"]
        self.last_raw_id = id
        self.raw_data_dict[id] = {
            "id": id,
            "phase": "observation",
            "algorithm": OPTIMIZER_NAME,
            "x": new_production_data["x"]["conveyorRuntime"],
            #            'y': new_production_data['y']
        }
        # if new_production_data["phase"] == "init":
        #     print("Production still in init phase")
        #     return

        if new_production_data["cycle"] < 5:
            print("Production still in init phase")
            return

        # instantiate optimizer
        alg = OptAlgorithm(self.bounds, OPTIMIZER_NAME,
                           OPTIMIZER_PARAMETERS)
        result = alg.run(self.apply_on_cpps)
        x = result.x[0]
        y = None
        if isinstance(result.fun, (np.float, np.float64)):
            y = result.fun
        else:
            y = result.fun[0]

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
        application_results = {
            "phase": "observation",
            "algorithm": OPTIMIZER_NAME,
            "id": new_production_data["cycle"],
            "x": x,
            "y": y,
        }

        self.send_msg(topic="AB_application_results",
                      message=application_results)


env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}


"""
def evaluate_diff_evo(x):
    X = np.array(x).reshape(-1, 1)
    res = model.predict(X)

    return res[0].item()
"""
new_pc = Optimizer(**env_vars)
OPTIMIZER_NAME = new_pc.config["OPTIMIZER_NAME"]

API_URL = new_pc.config["API_URL"]
OPTIMIZER_PARAMETERS = new_pc.get_optimizer_parameters(API_URL)


try:
    while True:
        msg = new_pc.consumer.poll(0.1)

        if msg is None:
            continue

        elif msg.error() is not None:
            print(f"Error occured: {str(msg.error())}")

        else:
            new_pc.func_dict[msg.topic()](msg)
            # new_message = new_pc.decode_msg(msg)
            # print(f"Received on topic '{msg.topic()}': {new_message}")

except KeyboardInterrupt:
    pass

finally:
    new_pc.consumer.close()

# for msg in new_pc.consumer:
#     new_pc.func_dict[msg.topic](msg)
