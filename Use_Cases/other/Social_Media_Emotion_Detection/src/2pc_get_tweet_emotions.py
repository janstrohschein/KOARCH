import sys
import os
from configparser import ConfigParser
import pprint
import time
from classes.KafkaPC import KafkaPC
from emotion_recognition_master.emotion_predictor import EmotionPredictor


class GetEmotionsPC(KafkaPC):
    def __init__(self, config_path=None, in_topic=None, in_group=None, in_schema_file=None, out_topic=None, out_schema_file=None):
        super().__init__(config_path, in_topic, in_group, in_schema_file, out_topic, out_schema_file)

        print('Load Model')
        self.model = EmotionPredictor(classification='ekman', setting='mc')
        print('Model loaded')


env_vars = {'in_topic': os.getenv('IN_TOPIC'),
            'in_group': os.getenv('IN_GROUP'),
            'in_schema_file': os.getenv('IN_SCHEMA_FILE'),
            'out_topic': os.getenv('OUT_TOPIC'),
            'out_schema_file': os.getenv('OUT_SCHEMA_FILE')}

new_pc = GetEmotionsPC(**env_vars)

for msg in new_pc.consumer:
    new_tweet = new_pc.decode_avro_msg(msg)
    
    result = new_pc.model.predict_probabilities([new_tweet['text']])

    new_tweet['anger'] = float(result.Anger.values[0])
    new_tweet['disgust'] = float(result.Disgust.values[0])
    new_tweet['fear'] = float(result.Fear.values[0])
    new_tweet['joy'] = float(result.Joy.values[0])
    new_tweet['sadness'] = float(result.Sadness.values[0])
    new_tweet['surprise'] = float(result.Surprise.values[0])

    new_pc.send_msg(new_tweet)
    print(new_tweet['author_id_str'], new_tweet['status_id_str'])