# Import the necessary methods from tweepy library
from tweepy import OAuthHandler
from tweepy import API

from classes.KafkaPC import KafkaPC


class TwitterP(KafkaPC):
    def __init__(self, config_path=None, in_topic=None, in_group=None,
                 in_schema_file=None, out_topic=None, out_schema_file=None):
        super().__init__(config_path, in_topic, in_group, in_schema_file,
                         out_topic, out_schema_file)

        auth = OAuthHandler(*self.config['Twitter']['consumer_key'],
                            *self.config['Twitter']['consumer_secret'])

        auth.set_access_token(*self.config['Twitter']['access_token'],
                              *self.config['Twitter']['access_token_secret'])

        self.api = API(auth, wait_on_rate_limit=True)
