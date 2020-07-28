import sys
import io
import yaml

from kafka import KafkaProducer, KafkaConsumer
from kafka.structs import OffsetAndMetadata, TopicPartition
from avro.io import BinaryEncoder, DatumWriter
import avro.schema


class KafkaPC():
    def __init__(self, config_path, config_section):
        super(KafkaPC, self).__init__()

        self.config = {}
        if config_path is not None and config_section is not None:
            config_section = config_section.replace(' ', '').split(',')
            self.read_config(config_path, config_section)

        if self.config.get('IN_TOPIC') and self.config.get('IN_GROUP'):
            self.consumer = KafkaConsumer(group_id=self.config['IN_GROUP'],
                                          bootstrap_servers=[self.config['KAFKA_BROKER_URL']],
                                          )
            self.in_topic = list(self.config['IN_TOPIC'].keys())
            self.consumer.subscribe(self.in_topic)

            self.in_schema = {}
            for topic, schema in self.config['IN_TOPIC'].items():
                self.in_schema[topic] = self.read_avro_schema(schema)

        if self.config.get('OUT_TOPIC'):
            self.out_topic = list(self.config['OUT_TOPIC'].keys())
            self.out_schema = {}
            for topic, schema in self.config['OUT_TOPIC'].items():
                self.out_schema[topic] = self.read_avro_schema(schema)
            self.producer = KafkaProducer(linger_ms=50, bootstrap_servers=[self.config['KAFKA_BROKER_URL']])

    def read_config(self, config_path, config_section):
        try:
            with open(config_path, "r") as ymlfile:
                config = yaml.load(ymlfile, Loader=yaml.FullLoader)
                for section in config_section:
                    for key, value in config[section].items():
                        self.config[key] = value

        except Exception as e:
            print(f'Failed to read the config: {repr(e)}')
            sys.exit()

    def read_avro_schema(self, schema):
        return avro.schema.Parse(open(schema).read())

    """ can we delete this function, if we don´t want to send messages WITHOUT schema?
    def decode_msg(self, msg):
        try:
            decoded = msg.value.decode("utf-8")
            return decoded
        except Exception as e:
            print(f'Error decoding data: {repr(e)}')
            sys.exit()
    """
    def decode_avro_msg(self, msg):
        try:
            bytes_reader = io.BytesIO(msg.value)
            decoder = avro.io.BinaryDecoder(bytes_reader)
            reader = avro.io.DatumReader(self.in_schema[msg.topic])
            return reader.read(decoder)
        except Exception as e:
            print(f'Error decoding avro data: {repr(e)}')
            sys.exit()

    def __encode(self, data, schema):

        raw_bytes = None
        try:
            writer = DatumWriter(schema)
            bytes_writer = io.BytesIO()
            encoder = BinaryEncoder(bytes_writer)
            writer.write(data, encoder)
            raw_bytes = bytes_writer.getvalue()

        except Exception as e:
            print(f'Error encoding data: {repr(e)}')

        return raw_bytes

    def send_msg(self, data, key=0, topic=None):

        # if no topic is provided, the first topic in the list is used as default
        if topic is None:
            out_topic = self.out_topic[0]
        else:
            out_topic = topic

        schema = self.out_schema[out_topic]
        # encode the data with the specified Avro out_schema
        raw_bytes = self.__encode(data, schema)

        # publish the message if encoding was successful
        if raw_bytes is not None:
            try:
                self.producer.send(out_topic, raw_bytes, partition=key)
            except Exception as e:
                print(f'Error sending data to Kafka: {repr(e)}')

    def commit_offset(self, msg):
        tp = TopicPartition(msg.topic, msg.partition)
        offsets = {tp: OffsetAndMetadata(msg.offset, None)}
        self.consumer.commit(offsets=offsets)
