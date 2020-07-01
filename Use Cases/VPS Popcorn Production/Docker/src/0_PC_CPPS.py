import requests
import json
import time

import os
from classes.KafkaPC import KafkaPC
from classes.util import ObjectiveFunction


env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

"""
env_vars = {#'in_topic': 'adaption',
            #'in_group': 'CPPS',
            #'in_schema_file': './schema/new_x.avsc',
            'out_topic': 'DB_raw_data',
            'out_schema_file': './schema/data.avsc'}
"""

new_objective = ObjectiveFunction()
new_objective.load_data()
new_objective.fit_model()

new_pc = KafkaPC(**env_vars)

N_INITIAL_DESIGN = 5
MAX_DATA_POINTS = 50 + N_INITIAL_DESIGN
phase = 'init'
current_data_point = 0

time.sleep(5)

while current_data_point < MAX_DATA_POINTS:

    if current_data_point == N_INITIAL_DESIGN - 1:
        phase = 'observation'

    # API_URL = "http://127.0.0.1:8000"
    API_URL = new_pc.config['API_URL']
    ENDPOINT = "/production_parameter/x"
    URL = API_URL + ENDPOINT

    print("The CPPS loads the current value for x from the CPPS Controller")
    api_request = requests.get(url=URL)
    new_x = json.loads(api_request.content)
    new_y = new_objective.get_objective(new_x)

    new_data_point = {'phase': phase,
                      'id_x': current_data_point,
                      'x': new_x,
                      'y': new_y}

    new_pc.send_msg(new_data_point)
    print(f"The CPPS produced with x={round(new_x, 3)} and got y={round(new_y, 3)}")
    current_data_point += 1
    time.sleep(5)
