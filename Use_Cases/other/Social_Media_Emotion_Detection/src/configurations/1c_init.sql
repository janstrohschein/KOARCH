CREATE TABLE twitter_users(
 user_id VARCHAR(20) PRIMARY KEY,
 user_name VARCHAR,
 user_location VARCHAR,
 account_created_at TIMESTAMP,
 statuses_count INTEGER,
 favorites_count INTEGER,
 followers_count INTEGER,
 friends_count INTEGER,
 verified BOOLEAN
);