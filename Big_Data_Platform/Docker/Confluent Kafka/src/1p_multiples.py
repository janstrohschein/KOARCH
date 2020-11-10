import time

from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField

print("start 1p_multiples")

broker = 'kafka:9093'
topic = 'multiples'
conf = {'bootstrap.servers': broker}

p = Producer(**conf)
s = StringSerializer()
print("created KafkaPC")

ctx = SerializationContext(topic, MessageField.VALUE)
for i in range(10):

    # casts int to string for StringSerializer/StringDeserializer
    message = s(str(i*i), ctx)

    # DeprecationWarning will be resolved in upcoming release
    # https://github.com/confluentinc/confluent-kafka-python/issues/763
    p.produce(topic, message)

    print(f"Sent message {i*i}")
    time.sleep(1)
