import os
from time import sleep

import pandas as pd

from Use_Cases.VPS_Popcorn_Production.Kubernetes.src.classes.CognitionPC import CognitionPC

pd.set_option("display.max_columns", None)
pd.options.display.float_format = "{:.3f}".format

debugging = False

if debugging is True:
    env_vars = {
        "config_path": "./Use_Cases/VPS_Popcorn_Production/Kubernetes/src/configurations/config_local.yml",
        "config_section": "General, Initial_Design, Objective_Function, 3_pc_evaluation"
    }
else:
    env_vars = {
        "config_path": os.getenv("config_path"),
        "config_section": os.getenv("config_section"),
    }


new_cog = CognitionPC(**env_vars)


sleep(3)

print(
    f"Creating initial design of the system by applying {new_cog.N_INITIAL_DESIGN} equally distributed\n"
    f"values x over the whole working area of the CPPS."
    f"\nSend x={new_cog.X[new_cog.nr_of_iterations]} to Adaption."
)

"""
"name": "New X",
"fields": [
    {"name": "algorithm", "type": ["string"]},
     {"name": "new_x", "type": ["float"]}
 ]
"""
new_cog.send_point_from_initial_design()
new_cog.nr_of_iterations += 1

try:
    while True:
        msg = new_cog.consumer.poll(0.1)

        if msg is None:
            continue

        elif msg.error() is not None:
            print(f"Error occured: {str(msg.error())}")

        else:
            try:
                topic = msg.topic()
            except Exception as e:
                print(f"Error retrieving topic: {repr(e)}")
            try:
                new_message = new_cog.decode_msg(msg)
                print(f"Received on topic '{msg.topic()}': {new_message}")
            except Exception as e:
                print(
                    f"Error decoding msg: {msg.topic()}, message: {new_message}")
                print(f"Error: {repr(e)}")
            try:
                new_cog.func_dict[msg.topic()](msg)
            except Exception as e:
                print(
                    f"Error accessing the function for topic {msg.topic()}: {repr(e)}")

except KeyboardInterrupt:
    pass


finally:
    new_cog.consumer.close()

# for msg in new_cog.consumer:
#     new_cog.func_dict[msg.topic](msg)
