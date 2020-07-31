import os
import requests
import json
from classes.KafkaPC import KafkaPC


def process_topics(msg):

    new_message = new_c.decode_avro_msg(msg)
    ENDPOINT_PARAMETER = msg.topic

    param_str = json.dumps(new_message)
    params = {"row": param_str}

    URL = API_URL + ENDPOINT + ENDPOINT_PARAMETER

    requests.post(url=URL, params=params)


env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}


func_dict = {"AB_model_application": process_topics,
             "AB_monitoring": process_topics,
             "AB_model_evaluation": process_topics}

new_c = KafkaPC(**env_vars)

API_URL = new_c.config['API_URL']
ENDPOINT = "/topic/"

for msg in new_c.consumer:

    func_dict[msg.topic](msg)
