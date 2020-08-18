import os
from classes.KafkaPC import KafkaPC


env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

"""
env_vars = {'in_topic': os.getenv('IN_TOPIC'),
            'in_group': os.getenv('IN_GROUP'),
            'in_schema_file': os.getenv('IN_SCHEMA_FILE'),
            'out_topic': os.getenv('OUT_TOPIC'),
            'out_schema_file': os.getenv('OUT_SCHEMA_FILE')}


env_vars = {'in_topic': {'DB_raw_data': './schema/data.avsc'},
            'in_group': 'monitoring',
            'in_schema_file': './schema/data.avsc',
            'out_topic': 'AB_monitoring',
            'out_schema_file': './schema/monitoring.avsc',
            'config_path': 'config.yaml'}
"""

new_pc = KafkaPC(**env_vars)


for msg in new_pc.consumer:
    """
    "name": "Data",
    "fields": [
        {"name": "phase", "type": ["string"]},
        {"name": "id_x", "type": ["int"]},
        {"name": "x", "type": ["float"]},
        {"name": "y", "type": ["float"]}
        ]
    """
    new_data = new_pc.decode_avro_msg(msg)

    """
    "name": "Data",
    "fields": [
        {"name": "phase", "type": ["string"]},
        {"name": "id_x", "type": ["int"]},
        {"name": "x", "type": ["float"]},
        {"name": "y", "type": ["float"]}
        ]
    """

    new_data_point = {'phase': new_data['phase'],
                      'id': new_data['id'],
                      'x': new_data['x'],
                      'y': new_data['y']}

    new_pc.send_msg(new_data_point)
