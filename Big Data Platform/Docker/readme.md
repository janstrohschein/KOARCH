# Big Data Platform in Docker

The components of the big data platform are various software building blocks, each implemented in a Docker container.
Modules do not communicate directly with each other, but use messaging to publish and subscribe to relevant topics.

# Docker Installation
Please install Docker and docker-compose to run the containers.
You find instructions for the Docker installation at their [website](https://docs.docker.com/get-docker/). To test the Docker installation you can open a terminal and execute `docker run hello-world`.

On some OS the Docker installation does not include docker-compose. You can find information for the installation [here](https://docs.docker.com/compose/install/)  if you get a message that docker-compose is missing.

# Building blocks

## Kafka
Kafka consists of brokers, producers and consumers. A producer publishes a message to a certain topic and sends it to the broker. A consumer subscribes to a topic and receives incoming messages.

Before we start the Kafka broker we create a network, for easier communication between containers, by running this command in a terminal:\
`docker network create caai`

Now you can start the Kafka broker with the following command:\
`docker-compose -f docker-compose_kafka.yml up`

This starts the Kafka container and an additional Zookeeper container, which helps Kafka to handle state. Docker also  opens port 9092 for communication between localhost and the container and 9093 for communication between containers.

Open two additional terminals and execute the commands below to send and receive messages:
`docker-compose -f docker-compose_1p_count_up up`
`docker-compose -f docker-compose_2c_print_out up`
