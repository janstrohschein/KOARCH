import os
import requests
from classes.KafkaPC import KafkaPC

"""
- leitet das neue X an das CPPS zur Auswertung weiter

"""

env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

"""
env_vars = {'kafka_broker_url': os.getenv('KAFKA_BROKER_URL'),
            'in_topic': os.getenv('IN_TOPIC'),
            'in_group': os.getenv('IN_GROUP'),
            'in_schema_file': os.getenv('IN_SCHEMA_FILE'),
            'out_topic': os.getenv('OUT_TOPIC'),
            'out_schema_file': os.getenv('OUT_SCHEMA_FILE')}
"""

""" lokal
env_vars = {'in_topic': 'AB_model_evaluation',
            'in_group': 'adaption',
            'in_schema_file': './schema/new_x.avsc',
            'out_topic': 'adaption',
            'out_schema_file': './schema/new_x.avsc'
            }

API_URL = "http://127.0.0.1:8000"
"""

new_pc = KafkaPC(**env_vars)

API_URL = new_pc.config['API_URL']
ENDPOINT = "/production_parameter/x"
URL = API_URL + ENDPOINT


for msg in new_pc.consumer:
    """
    "name": "New X",
    "fields": [
        {"name": "phase", "type": ["string"]},
        {"name": "id_x", "type": ["int"]},
        {"name": "new_x", "type": ["float"]}
        ]
    """

    new_message = new_pc.decode_avro_msg(msg)
    # new_pc.commit_offset(msg)

    # new_pc.send_msg(new_message)
    # print('The value x='+str(new_message['new_x'])+' is applied to the CPPS')

    # defining a params dict for the parameters to be sent to the API
    params = {"value": new_message['new_x']}

    # sending get request and saving the response as response object
    print(f"The Adaption sent x={round(new_message['new_x'], 3)} to the CPPS Controller")
    r = requests.put(url=URL, params=params)
