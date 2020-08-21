import os

from classes.PostgresPC import PostgresPC

env_vars = {'in_topic': os.getenv('IN_TOPIC'),
            'in_group': os.getenv('IN_GROUP'),
            'in_schema_file': os.getenv('IN_SCHEMA_FILE'),
            'config_path': os.getenv('CONFIG_PATH')}

new_c = PostgresPC(**env_vars)

sql = "INSERT INTO twitter_updates(status_id, user_id, status_created_at, text, retweet_count, \
    anger, disgust, fear, joy, sadness, surprise) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT \
    (status_id) DO NOTHING;"


for msg in new_c.consumer:
    new_emo = new_c.decode_avro_msg(msg)

    row_values = (new_emo['status_id_str'], new_emo['author_id_str'], new_emo['status_created_at_str'],
                  new_emo['text'], new_emo['retweet_count'], new_emo['anger'],
                  new_emo['disgust'], new_emo['fear'], new_emo['joy'],
                  new_emo['sadness'], new_emo['surprise'], )

    try:
        new_c.cur.execute(sql, row_values)
    except Exception as e:
        print(f"Could not insert status {new_emo['status_id_str']} from {new_emo['author_id_str']}"
              f"Error {e}"
              )

    # print('Insert status', new_emo['status_id_str'], 'from', new_emo['author_id_str'])
