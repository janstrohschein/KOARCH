import os
import pickle
import numpy as np
import sys
import warnings

import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
import rpy2.rinterface_lib.callbacks

from Big_Data_Platform.Kubernetes.Kafka_Client.Confluent_Kafka_Python.src.classes.CKafkaPC import KafkaPC
from Use_Cases.VPS_Popcorn_Production.Kubernetes.src.classes.caai_util import DataWindow


if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

debugging = False

if debugging is True:
    prefix = "Use_Cases/VPS_Popcorn_Production/Kubernetes/src/"
    env_vars = {
        "config_path": "./Use_Cases/VPS_Popcorn_Production/Kubernetes/src/configurations/config_local.yml",
        "config_section": "General, 3_pc_simulation"
    }
else:
    prefix = ""
    env_vars = {
        "config_path": os.getenv("config_path"),
        "config_section": os.getenv("config_section"),
    }


class Simulation(KafkaPC):
    def __init__(self, config_path, config_section):
        super().__init__(config_path, config_section)
        self.stdout = []
        self.stdout_orig = None
        self.stderr_orig = None

    def add_to_stdout(self, line):
        self.stdout.append(line)

    def capture_r_console_output(self):
        self.stdout = []  # reset buffer

        # Keep the old function
        self.stdout_orig = rpy2.rinterface_lib.callbacks.consolewrite_print
        self.stderr_orig = rpy2.rinterface_lib.callbacks.consolewrite_warnerror

        # redirect output
        rpy2.rinterface_lib.callbacks.consolewrite_print = self.add_to_stdout
        rpy2.rinterface_lib.callbacks.consolewrite_warnerror = self.add_to_stdout

    def reset_r_console_output(self):
        print("reset buffer")
        self.stdout = []
        rpy2.rinterface_lib.callbacks.consolewrite_print = self.stdout_orig
        rpy2.rinterface_lib.callbacks.consolewrite_warnerror = self.stderr_orig


new_pc = Simulation(**env_vars)

new_window = DataWindow()
MIN_DATA_POINTS = 5

X_MIN = 4000
X_MAX = 10100
BUDGET = 20
N_INSTANCES = new_pc.config["N_INSTANCES"]
print("N_INSTANCES to simulate: " + str(N_INSTANCES))

generate_new = False

# selection_phase = 0

# rpy2 r objects access
r = robjects.r

# redirect r output to local buffer
new_pc.capture_r_console_output()

# source R file of test functions generator implementation
source_simulation_r = prefix + "L3_PC_Simulation.R"
r.source(source_simulation_r)

# enable r data.frame to pandas conversion
pandas2ri.activate()

try:
    while True:
        msg = new_pc.consumer.poll(0.1)

        if msg is None:
            continue

        elif msg.error() is not None:
            print(f"Error occured: {str(msg.error())}")

        else:
            # new_message = new_pc.decode_msg(msg)
            # print(f"Received on topic '{msg.topic()}': {new_message}")
            """
            Incoming AVRO Message:
            {"type": "record",
            "name": "Simulation_Data",
            "fields": [
                {"name": "id", "type": ["int"]},
                {"name": "selection_phase", "type": ["int"]},
                {"name": "new_simulation", "type": ["bool"]},
                {"name": "x", "type": ["float"]},
                {"name": "y", "type": ["float"]}
                ]
                }
            """
            new_data = new_pc.decode_msg(msg)
            new_data_point = new_window.Data_Point(
                new_data["id"], new_data["x"], new_data["y"]
            )
            new_window.append_and_check(new_data_point)

            # print(new_data)
            if new_data["new_simulation"] is True:
                generate_new = True
            if len(new_window.data) < MIN_DATA_POINTS:
                print(
                    f"Collecting training data for Test function generator "
                    f"({len(new_window.data)}/{MIN_DATA_POINTS})"
                )
            elif generate_new is True:
                # reset generation request
                generate_new = False

                # take x/y to instantiate R simulator with nr_instances
                generateTestFunctions = robjects.r["generateTestFunctions"]

                df = new_window.to_df()

                print(df)

                testInstance = generateTestFunctions(df, N_INSTANCES)
                # compute baseline performance results and send to cognition
                # selection_phase = selection_phase + 1
                repetition = 1
                # TODO Resources for Baseline necessary? Set to 0?
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
                    "selection_phase": new_data["selection_phase"],
                    "algorithm": "baseline",
                    "repetition": repetition,
                    "budget": BUDGET,
                    "x": best_x,
                    "y": best_y,
                }
                print("Sending Baseline to Cognition")
                new_pc.send_msg(
                    topic="AB_simulation_results", message=simulation_result_data
                )

                objective_pickle = pickle.dumps(testInstance)
                simulation_data = {
                    "id": new_data["id"],
                    "selection_phase": new_data["selection_phase"],
                    "simulation": objective_pickle}
                print("Sending Test function")
                new_pc.send_msg(topic="AB_test_function",
                                message=simulation_data)

except KeyboardInterrupt:
    pass

finally:
    new_pc.consumer.close()

# for msg in new_pc.consumer:

#     """
#     Incoming AVRO Message:
#     {"type": "record",
#     "name": "Simulation_Data",
#     "fields": [
#         {"name": "id", "type": ["int"]},
#         {"name": "new_simulation", "type": ["bool"]},
#         {"name": "x", "type": ["float"]},
#         {"name": "y", "type": ["float"]}
#         ]
#         }
#     """
#     new_data = new_pc.decode_msg(msg)
#     new_data_point = new_window.Data_Point(new_data["id"], new_data["x"], new_data["y"])
#     new_window.append_and_check(new_data_point)

#     # print(new_data)
#     if new_data["new_simulation"] == True:
#         generate_new = True
#     if len(new_window.data) < MIN_DATA_POINTS:
#         print(
#             f"Collecting training data for Test function generator "
#             f"({len(new_window.data)}/{MIN_DATA_POINTS})"
#         )
#     elif generate_new == True:
#         # reset generation request
#         generate_new = False
#         # TODO consider theta, etha, count iteration
#         # take x/y to instantiate R simulator with nr_instances
#         generateTestFunctions = robjects.r["generateTestFunctions"]

#         df = new_window.to_df()

#         testInstance = generateTestFunctions(df, N_INSTANCES)
#         # compute baseline performance results and send to cognition
#         selection_phase = 1
#         repetition = 1
#         CPU_ms = 0.1
#         RAM = 0.05
#         samples = np.random.uniform(low=X_MIN, high=X_MAX, size=BUDGET)
#         y = testInstance(samples)
#         best_y = min(y)
#         best_id = np.argmin(y)
#         best_x = samples[best_id]

#         """
#          "name": "Simulation_Result",
#         "fields": [
#             {"name": "selection_phase", "type": ["int"]},
#             {"name": "algorithm", "type": ["string"]},
#             {"name": "repetition", "type": ["int"]},
#             {"name": "budget", "type": ["int"]},
#             {"name": "x", "type": ["float"]},
#             {"name": "y", "type": ["float"]},
#             {"name": "CPU_ms", "type": ["float"]},
#             {"name": "RAM", "type": ["float"]}
#             ]
#         """
#         simulation_result_data = {
#             "selection_phase": selection_phase,
#             "algorithm": "baseline",
#             "repetition": repetition,
#             "budget": BUDGET,
#             "x": best_x,
#             "y": best_y,
#             "CPU_ms": CPU_ms,
#             "RAM": RAM,
#         }
#         print("Sending Baseline to Cognition")
#         new_pc.send_msg(topic="AB_simulation_results", data=simulation_result_data)

#         objective_pickle = pickle.dumps(testInstance)
#         simulation_data = {"id": new_data["id"], "simulation": objective_pickle}
#         print("Sending Test function")
#         new_pc.send_msg(topic="AB_test_function", data=simulation_data)

# reset r output redirects
# new_pc.reset_r_console_output()
