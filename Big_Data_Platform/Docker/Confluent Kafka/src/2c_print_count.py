import os

from classes.CKafkaPC import KafkaPC

print("start 2c_print_count")

env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

new_c = KafkaPC(**env_vars)
print("created KafkaPC")

try:
    while True:
        msg = new_c.consumer.poll(0.1)

        if msg is None:
            continue

        elif msg.error() is not None:
            print(f"Error occured: {str(msg.error())}")

        else:
            new_message = new_c.decode_avro_msg(msg)
            print(f"Received message: {new_message}")

except KeyboardInterrupt:
    pass

finally:
    new_c.consumer.close()
