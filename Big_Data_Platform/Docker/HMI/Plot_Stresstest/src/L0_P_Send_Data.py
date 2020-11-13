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

for row in data:
    print(row)
    new_pc.send_msg(row)
    sleep(0.1)
