import json
import os
from time import sleep
from classes.CKafkaPC import KafkaPC


def load_data(file):
    with open(file) as f:
        return json.load(f)


data = load_data("./data/plot_topic_200k_unfunktionabel.json")

env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

new_pc = KafkaPC(**env_vars)

max_iteration = 100
iteration = 0
message_count = 0
while iteration < max_iteration:
    iteration += 1
    for row in data:
        message_count += 1
        print(f"Iteration {iteration}, Message {message_count}")
        new_pc.send_msg(row)
        sleep(0.1)
