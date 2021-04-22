import os
import requests
from classes.KafkaPC import KafkaPC

env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

new_pc = KafkaPC(**env_vars)

API_URL = new_pc.config['API_URL']
ENDPOINT = "/production_parameter/x"
URL = API_URL + ENDPOINT


for msg in new_pc.consumer:
    """
    "name": "New X",
    "fields": [
        {"name": "algorithm", "type": ["string"]},
        {"name": "new_x", "type": ["float"]}
        ]
    """

    new_message = new_pc.decode_avro_msg(msg)

    # defining a params dict for the parameters to be sent to the API
    params = {"value": new_message['new_x']}

    # sending get request and saving the response as response object
    print(f"Send x={round(new_message['new_x'], 3)} to the CPPS Controller")
    r = requests.put(url=URL, params=params)
