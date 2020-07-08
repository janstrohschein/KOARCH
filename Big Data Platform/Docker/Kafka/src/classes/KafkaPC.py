import sys
import io
import os
from configparser import ConfigParser

from kafka import KafkaProducer, KafkaConsumer

from avro.io import BinaryEncoder, DatumWriter
import avro.schema


class KafkaPC():
    def __init__(self, kafka_broker_url="localhost:9092", config_path=None, in_topic=None, in_group=None, in_schema_file=None, out_topic=None,
                 out_schema_file=None):
        super(KafkaPC, self).__init__()

        self.config = {}
        if config_path is not None:
            self.read_config(config_path)

        KAFKA_BROKER_URL = kafka_broker_url

        self.in_topic = in_topic

        if in_topic and in_group:
            self.consumer = KafkaConsumer(in_topic, group_id=in_group, bootstrap_servers=[KAFKA_BROKER_URL])

        self.out_topic = out_topic

        if in_schema_file:
            self.in_schema_file = in_schema_file
            self.in_schema = self.read_avro_schema(self.in_schema_file)
        else:
            self.in_schema_file = None
            self.in_schema = None

        if out_schema_file:
            self.out_schema_file = out_schema_file
            self.out_schema = self.read_avro_schema(self.out_schema_file)
        else:
            self.out_schema_file = None
            self.out_schema = None

        # if no broker_id is provided the KafkaProducer will connect
        # on localhost:9092
        self.producer = KafkaProducer(linger_ms=500, bootstrap_servers=[KAFKA_BROKER_URL])


    def read_config(self, config_path):
        config = ConfigParser()
        config.read(config_path, encoding='utf-8')

        try:
            sections = config.sections()
            if len(sections) == 0:
                sys.exit()
            for section in sections:

                self.config[section] = {}
                for option in config.options(section):
                    self.config[section][option] = config.get(section, option).split(',')
        except:
            print("The config file path is not valid")
            sys.exit()

    def read_avro_schema(self, schema):
        return avro.schema.Parse(open(schema).read())

    def decode_msg(self, msg):
        try:
            decoded = msg.value.decode("utf-8")
            return decoded
        except:
            print("Error decoding data", sys.exc_info())

    def decode_avro_msg(self, msg):
        try:
            bytes_reader = io.BytesIO(msg.value)
            decoder = avro.io.BinaryDecoder(bytes_reader)
            reader = avro.io.DatumReader(self.in_schema)
            return reader.read(decoder)
        except:
            print("Error decoding avro data", sys.exc_info())

    def __encode(self, data, schema=None):
        if schema is None:
            out_schema = self.out_schema
        else:
            out_schema = schema

        raw_bytes = None
        try:
            writer = DatumWriter(out_schema)
            bytes_writer = io.BytesIO()
            encoder = BinaryEncoder(bytes_writer)
            writer.write(data, encoder)
            raw_bytes = bytes_writer.getvalue()
        except:
            print("Error encoding data", sys.exc_info())
        return raw_bytes

    def send_msg(self, data, topic=None, key=0, schema=None):
        # encode the data with the specified Avro out_schema
        raw_bytes = self.__encode(data, schema)
        if topic == None:
            out_topic = self.out_topic
        else:
            out_topic = topic

        # publish the message if encoding was successful
        if raw_bytes is not None:
            try:
                self.producer.send(out_topic, raw_bytes, partition=key)
            except:
                print("Error sending message to kafka: ", sys.exc_info())
