import sys
import os
import json
import io
import csv
import codecs
from configparser import ConfigParser
from random import randint


# Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API
from tweepy import Cursor

from classes.TwitterP import TwitterP


import pprint
import time

env_vars = {'in_topic': os.getenv('IN_TOPIC'),
            'in_group': os.getenv('IN_GROUP'),
            'in_schema_file': os.getenv('IN_SCHEMA_FILE'),
            'out_topic': os.getenv('OUT_TOPIC'),
            'out_schema_file': os.getenv('OUT_SCHEMA_FILE'),
            'config_path': os.getenv('CONFIG_PATH')}

new_pc = TwitterP(**env_vars)

i = 0
user_set = set()
#print(type(user_set))
for msg in new_pc.consumer:
    new_user = new_pc.decode_avro_msg(msg)

    if new_user['id_str'] in user_set:
        print('Skipped User', new_user['id_str'])
        continue

    user_set.add(new_user['id_str'])
    i += 1
    print('User', i, ':', new_user)
    #print(new_user)
    # apparently 3200 tweets is the maximum
    retrieve_last_tweets = 3200
    j = 0
    try:
        #for status in Cursor(new_pc.api.user_timeline, id=new_user['id_str']).items(retrieve_last_tweets):
        for page in Cursor(new_pc.api.user_timeline, id=new_user['id_str'], count=retrieve_last_tweets).pages():
            #print('getting pages')
            for status in page:
                #print('getting status')
                j += 1
                #print('Tweet', i, '@', status.created_at, ':\n', status.text, '\n\n')
                cleaned_text = ' '.join(status.text.split()).replace(',', '')
                cleaned_text = cleaned_text.encode('ascii', 'ignore').decode('ascii')
                new_tweet = {
                    'author_id_str': new_user['id_str'],
                    'status_id_str': str(status.id),
                    'status_created_at_str': str(status.created_at),
                    'text': cleaned_text,
                    'retweet_count': status.retweet_count
                }
                if j % 100 == 0:
                    print(f'User {i} Tweet: {j}')

                key = randint(0,4)

                new_pc.send_msg(new_tweet, key=key)
            #new_pc.send_msg(new_tweet)
            time.sleep(5)
        #print('User', i, 'Tweet:', j)
    except:
	    print('Could not retrieve user')