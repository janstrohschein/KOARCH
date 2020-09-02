import os

from classes.PostgresPC import PostgresPC

env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}

new_c = PostgresPC(**env_vars)

sql = "INSERT INTO twitter_users(user_id, user_name, user_location, account_created_at, statuses_count, favorites_count,\
    followers_count, friends_count, verified) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)\
    ON CONFLICT (user_id) DO NOTHING;"

for msg in new_c.consumer:
    new_user = new_c.decode_avro_msg(msg)
    print(f"Received user:\n{new_user}")

    row_values = (new_user['id_str'], new_user['user_name'], new_user['user_location'],
                  new_user['account_created_at'], new_user['statuses_count'], new_user['favorites_count'],
                  new_user['followers_count'], new_user['friends_count'], new_user['verified'])

    try:
        new_c.cur.execute(sql, row_values)
    except Exception as e:
        print(f"Exception: {e}")