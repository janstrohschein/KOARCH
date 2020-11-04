import json
import os
from time import sleep
from classes.KafkaPC import KafkaPC


def load_data(file):
    with open(file) as f:
        return json.load(f)


data = load_data("./data/data.json")

env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

new_pc = KafkaPC(**env_vars)

for topic, rows in data.items():
    # checks if topic is a valid outgoing topic as specified in config.yml
    if topic not in new_pc.out_topic:
        continue
    else:
        print(f"Topic: {topic}")
        for row in rows:
            print(row)
            new_pc.send_msg(row, topic=topic)
            sleep(0.5)
