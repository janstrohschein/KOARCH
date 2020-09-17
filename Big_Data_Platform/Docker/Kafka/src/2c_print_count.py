import os

from classes.KafkaPC import KafkaPC

print("start 2c_print_count")

env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

new_c = KafkaPC(**env_vars)
print("created KafkaPC")

for msg in new_c.consumer:
    new_message = new_c.decode_avro_msg(msg)

    print(f'Received message {new_message["count"]}')
