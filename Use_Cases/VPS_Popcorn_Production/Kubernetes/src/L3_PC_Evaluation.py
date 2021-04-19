import os
from time import sleep

import pandas as pd

# from classes.KafkaPC import KafkaPC
from classes.CognitionPC import CognitionPC

pd.set_option("display.max_columns", None)
pd.options.display.float_format = "{:.3f}".format

env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}

new_cog = CognitionPC(**env_vars)

"""
"name": "New X",
"fields": [
     {"name": "new_x", "type": ["float"]}
 ]
"""

sleep(3)

print(f"Creating initial design of the system by applying {new_cog.N_INITIAL_DESIGN} equally distributed\n"
      f"values x over the whole working area of the CPPS."
      f"\nSend x={new_cog.X[new_cog.current_data_point]} to Adaption."
      )

new_cog.send_point_from_initial_design()
new_cog.current_data_point += 1

for msg in new_cog.consumer:
    new_cog.func_dict[msg.topic](msg)
