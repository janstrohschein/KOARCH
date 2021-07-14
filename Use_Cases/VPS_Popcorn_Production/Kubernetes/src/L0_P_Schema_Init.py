import os
import sys

from Big_Data_Platform.Kubernetes.Kafka_Client.Confluent_Kafka_Python.src.classes.CKafkaPC import (
    KafkaPC,
)

env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}

new_pc = KafkaPC(**env_vars)

sys.exit(0)
