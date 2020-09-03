# PostgreSQL
[PostgreSQL](https://www.postgresql.org/) also known as Postgres is a free and open-source relational database management system written in C.

# Example
The example creates a persistent Docker volume, initializes the containerized Postgres DB with the provided schema and stores data received from Kafka. 

## Preparation
The implementation consists of several Docker containers, so please install Docker and docker-compose. 
Instructions can be found [here](https://github.com/janstrohschein/KOARCH/tree/master/Big_Data_Platform/Docker).
Please make sure that your Docker Settings allow to share the local filesystem with the container to create a persistent volume.
Since Docker 2.20 this has to be enabled manually, the instructions can be found [here](https://stackoverflow.com/questions/60754297/docker-compose-failed-to-build-filesharing-has-been-cancelled).

- Create Docker Network\
  `docker network create caai`
- Create Docker Volumes\
  `docker volume create 1c_postgres_volume`
- Initialize Postgres DBs
  - Execute the Docker Compose script to initialize the DBs\
    `docker-compose -f docker-compose_init_dbs.yml up --build -d`
  - Check if the DB initialization was successful
    - connect to Postgres container\
      `docker exec -it 1c_postgres_db /bin/bash`
    - connect to Postgres instance inside container\
      `psql -h localhost -p 5432 -U postgres`
    - show table definition for "Twitter Users"\
      `\dt`
    - close psql\
      `\q`
    - quit bash session inside container\
      `exit`
  - Stop the DB containers\
    `docker-compose -f docker-compose_init_dbs.yml down`
- Start Kafka Containers\
  `docker-compose -f docker-compose_kafka.yml up --build -d`

## Send user entries to Postgres DB
- Use Docker Compose to start the pipeline\
  `docker-compose up --build -d`
- check for incoming data points in PostgresDB "User DB"
  - connect to Postgres container\
    `docker exec -it 1c_postgres_db /bin/bash`
  - connect to DB\
    `psql -h localhost -p 5432 -U postgres`
  - show the number of users in the DB\
    `select count(*) from twitter_users;`
  - show the users and their statistics, press "q" to close the result screen\
    `select * from twitter_users;`
  - close psql\
    `\q`
  - quit bash session inside container\
    `exit`

## Shutdown Docker Containers
- Stop Kafka Containers\
    `docker-compose -f docker-compose_kafka.yml down`
- Stop other Containers and DB\
    `docker-compose down`
