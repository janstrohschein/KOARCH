import os
from classes.KafkaPC import KafkaPC

"""
- leitet das neue X an das CPPS zur Auswertung weiter

"""

env_vars = {'kafka_broker_url': os.getenv('KAFKA_BROKER_URL'),
            'in_topic': os.getenv('IN_TOPIC'),
            'in_group': os.getenv('IN_GROUP'),
            'in_schema_file': os.getenv('IN_SCHEMA_FILE'),
            'out_topic': os.getenv('OUT_TOPIC'),
            'out_schema_file': os.getenv('OUT_SCHEMA_FILE')}
"""
env_vars = {'in_topic': 'AB_model_evaluation',
            'in_group': 'adaption',
            'in_schema_file': './schema/new_x.avsc',
            'out_topic': 'adaption',
            'out_schema_file': './schema/new_x.avsc'
            }
"""

new_pc = KafkaPC(**env_vars)

for msg in new_pc.consumer:
    """
    "name": "New X",
    "fields": [
        {"name": "phase", "type": ["string"]},
        {"name": "id_x", "type": ["int"]},
        {"name": "new_x", "type": ["float"]}
        ]
    """

    new_x = new_pc.decode_avro_msg(msg)




    """
    "name": "New X",
    "fields": [
        {"name": "phase", "type": ["enum"]},
        {"name": "id_x", "type": ["int"]},
        {"name": "new_x", "type": ["float"]}
        ]
    """
    new_pc.send_msg(new_x)
    print('The value x='+str(new_x['new_x'])+' is applied to the CPPS')
