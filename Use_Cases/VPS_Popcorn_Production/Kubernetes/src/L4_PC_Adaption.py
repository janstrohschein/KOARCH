import os
import requests

from Big_Data_Platform.Kubernetes.Kafka_Client.Confluent_Kafka_Python.src.classes.CKafkaPC import KafkaPC

env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}

new_pc = KafkaPC(**env_vars)

API_URL = new_pc.config["API_URL"]
ENDPOINT = "/production_parameters/"
URL = API_URL + ENDPOINT

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

            # defining a params dict for the parameters to be sent to the API
            params = {"x": new_message["new_x"],
                      "algorithm": new_message["algorithm"]}

            # sending put request and saving the response as response object
            print(
                f"Send x={round(new_message['new_x'], 3)} to the CPPS Controller")
            r = requests.put(url=URL, json=params)

except KeyboardInterrupt:
    pass

finally:
    new_pc.consumer.close()
