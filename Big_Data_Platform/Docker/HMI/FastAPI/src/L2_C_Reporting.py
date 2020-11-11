import os
import requests
import json
from classes.CKafkaPC import KafkaPC


def forward_topic(msg):
    """ forwards the incoming message to the API endpoint """
    new_message = new_c.decode_msg(msg)
    ENDPOINT_PARAMETER = msg.topic()

    param_str = json.dumps(new_message)
    params = {"row": param_str}

    URL = API_URL + ENDPOINT + ENDPOINT_PARAMETER

    requests.post(url=URL, params=params)
    print("Sent message to API")


env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

new_c = KafkaPC(**env_vars)

func_dict = new_c.config['API_OUT']

API_URL = new_c.config['API_URL']
ENDPOINT = new_c.config['API_ENDPOINT']

try:
    while True:
        msg = new_c.consumer.poll(0.1)
        if msg is None:
            continue

        elif msg.error() is not None:
            print(f"Error occured: {str(msg.error())}")

        else:
            try:
                eval(func_dict[msg.topic()])(msg)
            except Exception as e:
                print(f"Processing Topic: {msg.topic()} with Function: {func_dict[msg.topic()]}\n Error: {e}")

except KeyboardInterrupt:
    pass

finally:
    new_c.consumer.close()
