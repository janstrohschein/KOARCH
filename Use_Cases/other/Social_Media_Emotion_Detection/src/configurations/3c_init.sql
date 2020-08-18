CREATE TABLE twitter_updates(
 status_id VARCHAR(20) PRIMARY KEY,
 user_id VARCHAR(20),
 status_created_at TIMESTAMP,
 text VARCHAR(280),
 retweet_count INTEGER,
 anger FLOAT(4),
 disgust FLOAT(4),
 fear FLOAT(4),
 joy FLOAT(4),
 sadness FLOAT(4),
 surprise FLOAT(4)
);