import os
import json
from confluent_kafka import Producer

from Big_Data_Platform.Kubernetes.Kafka_Client.Confluent_Kafka_Python.src.classes.CKafkaPC import KafkaPC

env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}

new_pc = KafkaPC(**env_vars)

try:
    while True:
        msg = new_pc.consumer.poll(0.1)

        if msg is None:
            continue

        elif msg.error() is not None:
            print(f"Error occured: {str(msg.error())}")

        else:
            """
            "name": "New X",
            "fields": [
                {"name": "algorithm", "type": ["string"]},
                {"name": "new_x", "type": ["float"]}
                ]
            """

            new_message = new_pc.decode_msg(msg)

            producer = Producer(
                {'bootstrap.servers': 'kafka-all-broker.default:29092'})

            msg = json.dumps(
                {'|var|CODESYS Control for Raspberry Pi SL.Application.GVL.varTime':
                    int(new_message["new_x"])})

            print(f"Sending to Topic CPPSadaption: {msg}")
            producer.produce("CPPSadaption", msg)
            producer.flush()


except KeyboardInterrupt:
    pass

finally:
    new_pc.consumer.close()
