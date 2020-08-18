import os

from classes.KafkaPC import KafkaPC

print("start 2c_print_count")

env_vars = {
    "kafka_broker_url": os.getenv("KAFKA_BROKER_URL"),
    "in_topic": os.getenv("IN_TOPIC"),
    "in_group": os.getenv("IN_GROUP"),
    "in_schema_file": os.getenv("IN_SCHEMA_FILE"),
}

new_c = KafkaPC(**env_vars)
print("created KafkaPC")

for msg in new_c.consumer:
    new_message = new_c.decode_avro_msg(msg)

    print(f'Received message {new_message["count"]}')
