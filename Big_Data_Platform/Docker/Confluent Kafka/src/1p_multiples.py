import os
import time

from classes.CKafkaPC import KafkaPC

print("start 1p_multiples")

env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

new_p = KafkaPC(**env_vars)
print("created KafkaPC")

for i in range(10):

    message = {"multiple": i*i}
    new_p.send_msg(message)
    print(f"Sent message {i*i}")
    time.sleep(1)
