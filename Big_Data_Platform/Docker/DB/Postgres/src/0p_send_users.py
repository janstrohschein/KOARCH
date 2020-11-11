import os
import time
from dataclasses import dataclass

from classes.CKafkaPC import KafkaPC


@dataclass
class User:
    id_str: str
    user_name: str
    user_location: str
    account_created_at: str
    statuses_count: int  # The number of Tweets (& retweets) issued by the user.
    favorites_count: int  # The number of Tweets this user has liked
    followers_count: int  # The number of followers this account currently has.
    friends_count: int  # The number of users this account is following
    verified: bool


env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}

new_pc = KafkaPC(**env_vars)

user_info = [
    User(
        id_str="1234",
        user_name="user1",
        user_location="Cologne",
        account_created_at="2020-08-25 12:32",
        statuses_count=5,
        favorites_count=12,
        followers_count=7,
        friends_count=2,
        verified=True,
    ),
    User(
        id_str="1235",
        user_name="user2",
        user_location="Duesseldorf",
        account_created_at="2020-08-27 08:27",
        statuses_count=3,
        favorites_count=1,
        followers_count=5,
        friends_count=9,
        verified=False,
    ),
    User(
        id_str="1236",
        user_name="user3",
        user_location="Bonn",
        account_created_at="2020-08-28 10:17",
        statuses_count=8,
        favorites_count=23,
        followers_count=9,
        friends_count=8,
        verified=True,
    ),
]

for user in user_info:
    author = {
        "id_str": user.id_str,
        "user_name": user.user_name,
        "user_location": user.user_location,
        "account_created_at": user.account_created_at,
        "statuses_count": user.statuses_count,
        "favorites_count": user.favorites_count,
        "followers_count": user.followers_count,
        "friends_count": user.friends_count,
        "verified": user.verified,
    }

    new_pc.send_msg(author)
    print(f"Sent user:\n{author}")
    time.sleep(3)
