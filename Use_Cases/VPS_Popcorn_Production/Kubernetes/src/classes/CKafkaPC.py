import sys
import yaml

from confluent_kafka import Producer, Consumer
from confluent_kafka.serialization import (
    SerializationContext,
    MessageField,
    StringDeserializer,
)
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import (
    AvroSerializer,
    AvroDeserializer,
    Schema,
)


class KafkaPC:
    def __init__(self, config_path, config_section):
        super(KafkaPC, self).__init__()

        self.in_topic = None
        self.out_topic = None
        self.in_schema = None
        self.out_schema = None

        self.read_config(config_path, config_section)
        self.connect_schema_registry()
        self.read_topics()
        self.create_serializer()
        self.create_deserializer()
        self.create_consumer()
        self.create_producer()

    def connect_schema_registry(self):

        if self.config.get("KAFKA_SCHEMA_REGISTRY_URL") is not None:
            sr_conf = {"url": self.config["KAFKA_SCHEMA_REGISTRY_URL"]}
            self.schema_registry = SchemaRegistryClient(sr_conf)
        else:
            raise ValueError("Need KAFKA_SCHEMA_REGISTRY_URL")

    def get_schema_from_registry(self, topic, suffix="-value"):
        response = None
        try:
            schema = self.schema_registry.get_latest_version(topic + suffix)
            response = schema.schema
        except Exception as e:
            print(f"Exception: {repr(e)}")
        return response

    def read_topics(self):

        if self.config.get("IN_TOPIC") and self.config.get("IN_GROUP"):
            self.in_topic = self.config["IN_TOPIC"]

            self.in_schema = {}
            for topic in self.in_topic:
                # try to get schema from registry
                schema = self.get_schema_from_registry(topic)
                # if no schema is found a simple string deserializer will be used, see line 87
                if schema is None:
                    self.in_schema[topic] = None
                else:
                    self.in_schema[topic] = schema

        if self.config.get("OUT_TOPIC"):
            self.out_topic = list(self.config["OUT_TOPIC"].keys())
            self.out_schema = {}
            for topic, schema in self.config["OUT_TOPIC"].items():
                self.out_schema[topic] = self.read_avro_schema(schema)

    def create_serializer(self):
        self.serializer = {}
        if self.out_topic is not None:
            for topic in self.out_topic:
                schema_str = self.out_schema[topic].schema_str
                self.serializer[topic] = AvroSerializer(
                    schema_str, self.schema_registry
                )

    def create_deserializer(self):
        self.deserializer = {}
        if self.in_topic is not None:
            for topic in self.in_topic:
                if self.in_schema[topic] is None:
                    self.deserializer[topic] = StringDeserializer("utf_8")
                else:
                    schema_str = self.in_schema[topic].schema_str
                    self.deserializer[topic] = AvroDeserializer(
                        schema_str, self.schema_registry
                    )

    def create_consumer(self):

        if self.config.get("IN_TOPIC") and self.config.get("IN_GROUP"):

            consumer_conf = {
                "bootstrap.servers": self.config["KAFKA_BROKER_URL"],
                "group.id": self.config["IN_GROUP"],
                "auto.offset.reset": "earliest",
            }

            self.consumer = Consumer(consumer_conf)
            self.consumer.subscribe(self.in_topic)

    def create_producer(self):
        if self.config.get("OUT_TOPIC"):
            producer_conf = {"bootstrap.servers": self.config["KAFKA_BROKER_URL"]}
            self.producer = Producer(producer_conf)

    def read_config(self, config_path, config_section):
        self.config = {}
        if config_path is not None and config_section is not None:
            config_section = config_section.replace(" ", "").split(",")
        else:
            raise ValueError("Configuration requires config_path and config_section")
        try:
            with open(config_path, "r") as ymlfile:
                config = yaml.load(ymlfile, Loader=yaml.FullLoader)
                for section in config_section:
                    for key, value in config[section].items():
                        self.config[key] = value

        except Exception as e:
            print(f"Failed to read the config: {repr(e)}")
            sys.exit()

    def read_avro_schema(self, schema):

        with open(schema, "r") as f:
            schema_str = f.read()
        avro_schema_str = Schema(schema_str, "AVRO")

        return avro_schema_str

    def decode_msg(self, msg):

        try:
            topic = msg.topic()
            value = self.deserializer[topic](msg.value(), None)
            return value
        except Exception as e:
            print(f"Error decoding avro data: {repr(e)}")
            sys.exit()

    def send_msg(self, message, partition=0, topic=None):

        # if no topic is provided, the first topic in the list is used as default
        if topic is None:
            out_topic = self.out_topic[0]
        else:
            out_topic = topic

        # encode the data with the specified Avro out_schema
        ctx = SerializationContext(out_topic, MessageField.VALUE)
        ser_message = self.serializer[out_topic](message, ctx)

        try:
            self.producer.produce(
                topic=out_topic, value=ser_message, partition=partition
            )
        except Exception as e:
            print(f"Error sending data to Kafka: {repr(e)}")
