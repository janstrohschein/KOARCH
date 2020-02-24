# Preparation

- Install Docker
- Create Network
  - create network emotion-detection
- Create Volumes
  - create volume 1c_postgres_volume
  - create volume 3c_postgres_volume
- Initialize DBs
  - docker-compose -f docker-compose_init_dbs.yml up --build
  - open a second console
    - psql -h localhost -p 54321 -U postgres
      \dt shows table twitter_users
    - psql -h localhost -p 54323 -U postgres
      \dt shows table twitter_updates
    - \q closes psql
  - strg + c stops the containers in first console



# Collect tweets and classifications

- Use Docker Compose to start the containers
  docker-compose up --build
- connect to first PostgresDB
  - select count(*) from twitter_users;
  - select * from twitter_users;
    - "q" closes the result screen

# Analysis



