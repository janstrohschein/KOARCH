# Introduction

This use case implements a first prototype of our big data platform and uses an automated approach to study the emotions of a larger group of social media users on Twitter over time. It is possible to extract emotions from the text of their status updates as shown by Tasoulis et al. and Colneric and Demsar ([Tasoulis et al., 2018](https://arxiv.org/abs/1804.00482), [Colneric & Demsar, 2018](https://ieeexplore.ieee.org/document/8295234)). This analysis is based on the work of Colneric and Demsar ([github](https://github.com/nikicc/twitter-emotion-recognition))and investigates if the emotions of users or groups of users become more negative over time as suggested by other studies.







# Preparation

The implementation consists of several Docker containers. Please follow the instructions on [Docker Docs](https://docs.docker.com/install/) to install Docker for your platform. Afterwards open a console and complete the following steps:

- Create Network
  
  ```
  create network emotion-detection
  ```
  
- Create Volumes
  
  ```
  create volume 1c_postgres_volume
  create volume 3c_postgres_volume
  ```
  
- Initialize DBs
  
  - Execute the Docker Compose script to initialize the DBs
    
    ```
    docker-compose -f docker-compose_init_dbs.yml up --build -d
    ```
  
  - Check if the DB initialization was successful
    
    - connect to first Postgres instance on Port 54321
    
      ```
      psql -h localhost -p 54321 -U postgres
      ```
    
    - show table definition
    
      ```
      \dt
      ```
    
    - close psql
    
      ```
      \q
      ```
    
    - repeat for second instance on Port 54323
    
    ```
    psql -h localhost -p 54323 -U postgres
    \dt
    ```
    
  - Stop the DB containers
  
    ```
    docker-compose -f docker-compose_init_dbs.yml down
    ```
  
- Start Kafka Containers

  ```
  docker-compose -f docker-compose_kafka.yml up --build -d
  ```

  

# Collect tweets and classifications

- Use Docker Compose to start the containers
  docker-compose up --build
- connect to first PostgresDB
  - select count(*) from twitter_users;
  - select * from twitter_users;
    - "q" closes the result screen

# Analysis

The data can be analyzed in a Jupyter Notebook. We provide a sample notebook, but you can add notebooks in Python, R or Julia. 

- Start the Jupyter Hub Container

  ```
  docker-compose -f docker-compose_jupyter.yml -d
  ```

- Open Jupyter Hub in your browser at localhost:8888