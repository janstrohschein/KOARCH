import os
import json
from Big_Data_Platform.Kubernetes.Kafka_Client.Confluent_Kafka_Python.src.classes.CKafkaPC import KafkaPC
from confluent_kafka import Producer


debugging = True

if debugging is True:
    env_vars = {
        "config_path": "./Use_Cases/VPS_Popcorn_Production/Kubernetes/src/configurations/config_local.yml",
        "config_section": "General, Initial_Design, Objective_Function, 3_pc_evaluation"
    }
else:
    env_vars = {
        "config_path": os.getenv("config_path"),
        "config_section": os.getenv("config_section"),
    }


new_pc = KafkaPC(**env_vars)

print(new_pc)

producer = Producer({'bootstrap.servers': 'kafka-all-broker.default:29092'})

msg = json.dumps(
    {'|var|CODESYS Control for Raspberry Pi SL.Application.GVL_Dosing.VPS_Dosing.INST_Auger.O_xOn': int(7520.6)})

producer.produce("CPPSadaption", msg)
producer.flush()
