import sys
import os
import time
import logging

# Import the necessary methods from tweepy library
#from tweepy import OAuthHandler
#from tweepy import API
from tweepy import Cursor

from classes.TwitterP import TwitterP

def clean_string(input_string):

    if isinstance(input_string, str):
        cleaned_string = input_string.encode('ascii', 'ignore').decode('ascii')
        return cleaned_string
    else:
        return input_string

env_vars = {'config_path': os.getenv('CONFIG_PATH'),
            'out_topic': os.getenv('OUT_TOPIC'),
            'out_schema_file': os.getenv('OUT_SCHEMA_FILE')}


new_pc = TwitterP(**env_vars)

location = int(23424977)
tweet_count = 0
user_count = 0

user_set = set()
while True:
    trends = new_pc.api.trends_place(location)

    data = trends[0]
    location_info = data['locations'][0]
    location_name = location_info['name']
    location_woeid = location_info['woeid']

    # grab the trends
    trends = data['trends']
    tweets = []

    try:
        for trend in trends:
            #print(trend.get('name'))
            trend_tweets = new_pc.api.search(trend['query'])

            for tweet in trend_tweets:
                tweets.append(tweet)

    except:
        print("Error retrieving trend tweets", sys.exc_info())

    print('Got trends')

    for tweet in tweets:
        '''
        see documentation for user objects at
        https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/user-object.html 
        '''
        tweet_count += 1

        print('Tweet #', tweet_count)

        if tweet.author.id_str not in user_set:
            user_object_list = []
            user_set.add(tweet.author.id_str)
            user_count += 1
            print('User #', user_count, 'added: ', tweet.author.name)

            author = {
                'id_str' : tweet.author.id_str,
                'user_name': clean_string(tweet.author.name),
                'user_location': clean_string(tweet.author.location),
                'language': clean_string(tweet.author.lang),
                'account_created_at': str(tweet.author.created_at),
                'statuses_count': tweet.author.statuses_count,  # The number of Tweets (including retweets) issued by the user.
                'favorites_count': tweet.author.favourites_count, # The number of Tweets this user has liked in the account's lifetime.
                'followers_count': tweet.author.followers_count,  # The number of followers this account currently has.
                'friends_count': tweet.author.friends_count,  # The number of users this account is following
                'verified': tweet.author.verified
            }
            new_pc.send_msg(author)

            for page in Cursor(new_pc.api.followers, user_id=tweet.author.id_str).pages():
                for user in page:
                    if user.id_str not in user_set:
                        #print('Follower', 'added: ', user.name)
                        user_set.add(user.id_str)

                        following_user = {
                        'id_str': user.id_str,
                        'user_name': clean_string(user.name),
                        'user_location': clean_string(user.location),
                        'language': clean_string(user.lang),
                        'account_created_at': str(user.created_at),
                        'statuses_count': user.statuses_count, # The number of Tweets (including retweets) issued by the user.
                        'favorites_count': user.favourites_count, # The number of Tweets this user has liked in the account's lifetime.
                        'followers_count': user.followers_count, # The number of followers this account currently has.
                        'friends_count': user.friends_count,  # The number of users this account is following
                        'verified': user.verified
                        }
                        new_pc.send_msg(following_user)
                        #print('Sent user')
                        time.sleep(15)

                    else:
                        print('!!! Follower duplicate: ', user.name, '!!!')
        else:
            print('!!! User duplicate: ', tweet.author.name, '!!!')

        time.sleep(15)