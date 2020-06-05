import os
import time

from classes.KafkaPC import KafkaPC

print('start 1p_count_up')

env_vars = {'kafka_broker_url': os.getenv('KAFKA_BROKER_URL'),
            'out_topic': os.getenv('OUT_TOPIC'),
            'out_schema_file': os.getenv('OUT_SCHEMA_FILE')
            }

new_p = KafkaPC(**env_vars)
print('created KafkaPC')

for i in range(10):

    message = {"count" : i}
    new_p.send_msg(message)
    print(f'Sent message {i}')
    time.sleep(1)
