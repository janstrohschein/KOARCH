import os
import requests
import json
from classes.KafkaPC import KafkaPC


def forward_topic(msg):
    """ forwards the incoming message to the API endpoint """

    new_message = new_c.decode_avro_msg(msg)
    ENDPOINT_PARAMETER = msg.topic

    param_str = json.dumps(new_message)
    params = {"row": param_str}

    URL = API_URL + ENDPOINT + ENDPOINT_PARAMETER

    requests.post(url=URL, params=params)


def plot_data(msg):
    print('in plot_data')
    # ersetzen durch die Felder deines Schemas und die richtigen Felder der msg
    # anschließend Kommentar entfernen

    # new_data_point = {'plot': 'single',
    #                   'x': msg.new_x,
    #                   'y': msg.new_y}

    # new_c.send_msg(new_data_point)


def plot_data_multi(msg):
    print('in plot_data_multi')
    # ersetzen durch die Felder deines Schemas und die richtigen Felder der msg
    # anschließend Kommentar entfernen

    # new_data_point = {'plot': 'multi',
    #                   'x': msg.new_x,
    #                   'y': msg.new_y}

    # new_c.send_msg(new_data_point)


env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

new_c = KafkaPC(**env_vars)

api_dict = new_c.config['API_OUT']
plot_dict = new_c.config['PLOT_TOPIC']


API_URL = new_c.config['API_URL']
ENDPOINT = new_c.config['API_ENDPOINT']

for msg in new_c.consumer:
    # tests if msg.topic is in api_dict and calls function from dict
    try:
        if api_dict.get(msg.topic) is not None:
            eval(api_dict[msg.topic])(msg)
    except Exception as e:
        print(f"Processing Topic: {msg.topic} with Function: {api_dict[msg.topic]}\n Error: {e}")

    # tests if msg.topic is in plot_dict and calls function from dict
    try:
        if plot_dict.get(msg.topic) is not None:
            eval(plot_dict[msg.topic])(msg)
    except Exception as e:
        print(f"Processing Topic: {msg.topic} with Function: {plot_dict[msg.topic]}\n Error: {e}")
