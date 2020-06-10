import os
from classes.KafkaPC import KafkaPC
from classes.util import ObjectiveFunction


env_vars = {'kafka_broker_url': os.getenv('KAFKA_BROKER_URL'),
            'in_topic': os.getenv('IN_TOPIC'),
            'in_group': os.getenv('IN_GROUP'),
            'in_schema_file': os.getenv('IN_SCHEMA_FILE'),
            'out_topic': os.getenv('OUT_TOPIC'),
            'out_schema_file': os.getenv('OUT_SCHEMA_FILE')}
"""
env_vars = {'in_topic': 'adaption',
            'in_group': 'CPPS',
            'in_schema_file': './schema/new_x.avsc',
            'out_topic': 'DB_raw_data',
            'out_schema_file': './schema/data.avsc'}
"""

new_objective = ObjectiveFunction()
new_objective.load_data()
new_objective.fit_model()

new_pc = KafkaPC(**env_vars)


for msg in new_pc.consumer:
    """
    "name": "New_X",
    "fields": [
        {"name": "phase", "type": ["enum"], "symbols": ["init", "observation"]},
        {"name": "id_x", "type": ["int"]},
        {"name": "new_x", "type": ["float"]}
    ]
    """
    new_data = new_pc.decode_avro_msg(msg)
    new_x = new_data['new_x']
    new_y = new_objective.get_objective(new_x)

    new_data_point = {'phase': new_data['phase'],
                      'id_x': new_data['id_x'],
                      'x': new_x,
                      'y': new_y}

    new_pc.send_msg(new_data_point)
