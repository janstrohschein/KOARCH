import sys
import yaml
from time import sleep

from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient, NewTopic
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
        self.create_topics_on_broker()
        self.get_out_schema()
        self.register_schemas_in_registry()
        self.get_in_schema()
        self.create_serializer()
        self.create_deserializer()
        self.create_consumer()
        self.create_producer()

    def connect_schema_registry(self):
        MAX_RETRIES = 100

        if self.config.get("KAFKA_SCHEMA_REGISTRY_URL") is not None:
            sr_conf = {"url": self.config["KAFKA_SCHEMA_REGISTRY_URL"]}

            retries = 0
            while retries < MAX_RETRIES:
                try:
                    self.schema_registry = SchemaRegistryClient(sr_conf)
                    print("Connected to Schema Registry")
                    break
                except Exception as e:
                    retries += 1
                    print(
                        f"Could not connect to Schema Registry, retry {retries}")
                    print({repr(e)})
                    sleep(1)
            if retries == MAX_RETRIES:
                raise ConnectionError("Could not connect to Schema Registry")
        else:
            raise ValueError("Need KAFKA_SCHEMA_REGISTRY_URL")

    def register_schemas_in_registry(self, suffix="-value"):
        MAX_RETRIES = 100

        if self.out_schema is not None:
            for topic, schema in self.out_schema.items():
                subject = topic + suffix
                retries = 0
                while retries < MAX_RETRIES:
                    try:
                        self.schema_registry.register_schema(
                            subject_name=subject, schema=schema
                        )
                        print(
                            f"Registered schema for topic {topic} in registry")
                        break
                    except Exception as e:
                        retries += 1
                        print(
                            f"Could not register schema for topic {topic} in registry: {repr(e)}"
                        )
                        sleep(1)
                if retries == MAX_RETRIES:
                    raise ConnectionError(
                        "Could not connect to Schema Registry")

    def create_topics_on_broker(self, partitions=1, replication=1):

        if self.out_topic is not None:
            a = AdminClient(
                {"bootstrap.servers": self.config["KAFKA_BROKER_URL"]})

            topic_set = set(self.out_topic)

            md = a.list_topics(timeout=10)
            broker_set = set(md.topics.values())
            diff_set = topic_set.difference(broker_set)
            # print(f"Topics not yet available on Broker: {diff_set}")
            new_topics = [
                NewTopic(
                    topic, num_partitions=partitions, replication_factor=replication
                )
                for topic in diff_set
            ]

            fs = a.create_topics(new_topics)

            # Wait for operation to finish.
            # Timeouts are preferably controlled by passing request_timeout=15.0
            # to the create_topics() call.
            # All futures will finish at the same time.
            for topic, f in fs.items():
                try:
                    f.result()  # The result itself is None
                    print(f"Topic {topic} created on Broker")
                except Exception as e:
                    # print(f"Failed to create topic {topic} on Broker: {repr(e)}")
                    pass

    def get_schema_from_registry(self, topic, suffix="-value"):
        response = None

        MAX_RETRIES = 100
        retries = 0
        while retries < MAX_RETRIES:

            try:
                schema = self.schema_registry.get_latest_version(
                    topic + suffix)
                response = schema.schema
                print(f"Retrieved schema for topic {topic} from Registry")
                break
            except Exception as e:
                retries += 1
                # print(f"Failed to get schema: {repr(e)}")
                sleep(1)
        if retries == MAX_RETRIES:
            raise ConnectionError(
                f"Could not retrieve schema for topic {topic} from Registry"
            )
        return response

    def read_topics(self):

        if self.config.get("IN_TOPIC") and self.config.get("IN_GROUP"):
            self.in_topic = self.config["IN_TOPIC"]

        if self.config.get("OUT_TOPIC"):
            self.out_topic = list(self.config["OUT_TOPIC"].keys())

    def get_in_schema(self):
        if self.in_topic is not None:
            self.in_schema = {}
            for topic in self.in_topic:
                # try to get schema from registry
                schema = self.get_schema_from_registry(topic)
                # if no schema is found a simple string deserializer will be used, see line 87
                if schema is None:
                    self.in_schema[topic] = None
                else:
                    self.in_schema[topic] = schema

    def get_out_schema(self):
        if self.out_topic is not None:
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
            producer_conf = {
                "bootstrap.servers": self.config["KAFKA_BROKER_URL"]}
            self.producer = Producer(producer_conf)

    def read_config(self, config_path, config_section):
        self.config = {}
        if config_path is not None and config_section is not None:
            config_section = config_section.replace(" ", "").split(",")
        else:
            raise ValueError(
                "Configuration requires config_path and config_section")
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
            # sys.exit()

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
