# Kafka
Kafka consists of brokers, producers and consumers. 
A producer publishes a message to a certain topic and sends it to the broker. 
A consumer subscribes to a topic and receives incoming messages.

## General Workflow
The figure below depicts the workflow consisting of the following steps: 

1)	Start the Zookeeper server. This handles the orchestration between multiple Kafka Brokers and saves their state. If the restart of Kafka is necessary the last state can be restored so that all messages are processed correctly.
2)	Start the Kafka server. In a message-based infrastructure it is possible to have several Kafka Brokers on the same server or Brokers on multiple servers communicate with each other.
3) Start the Confluent Schema Registry. The Schema Registry manages the message schemas and enables schema evolution, which means the Schema Registry stores multiple versions for a schema if the data schema changes over time. Producers and Consumers can retrieve a specific version of the schema or the most recent version. More details on the Schema Registry can be found on the [Confluent Website](https://docs.confluent.io/current/schema-registry/index.html)
4) Instantiate a Producer and connect it to the Kafka Broker and the Schema Registry.
5) The Producer sends a message to the Broker. New messages can be created from various sources, for example the internet, databases, files or also production systems. 
The Kafka system uses the binary Avro format to encode the messages. Benefits of this approach are message compression and checks of data validity against the schema when it is encoded.
The Producer registers the schema for the messages with the Schema Registry. That allows to include the `schema_id` instead of the schema itself when sending new messages, which reduces the communication overhead.
6)	Instantiate a Consumer and connect it to the Kafka Broker and the Schema Registry.
The Consumer subscribes a specific topic from the Kafka Broker and retrieves the corresponding schema from the Schema Registry.
7)	Now the Consumer can process the data and create an intermediate result for further consumption or a final output.

<img src="./docs/kafka_workflow.jpg" width="609px">

## Example
Please install Docker and docker-compose to run the containers. 
Instructions can be found [here](https://github.com/janstrohschein/KOARCH/tree/master/Big_Data_Platform/Docker).
Before we start the Kafka broker we create a network, for easier communication between containers, by running this command in a terminal:\
`docker network create caai`

Now you can start the Kafka Broker and the Schema Registry with the following command:\
`docker-compose -f docker-compose_kafka.yml up`

Docker starts the containers and opens port 9092 for communication between localhost and the container and 9093 for communication between containers.
Additionally, the Schema Registry container gets created and is available via:\
`http://localhost:8081` on the host or\
`http://schema-registry:8081` for other containers.


Open two additional terminals and execute the commands below to send and receive messages:\
`docker-compose -f docker-compose_1p.yml up`\
`docker-compose -f docker-compose_2c_print.yml up`

You should see the first two programs, started through `docker-compose_1p.yml`, counting up or multiplying and sending those numbers to the broker.
The first program `1p_count_up.py` uses the schema `./schema/count.avsc` and registers the schema for the topic in the Schema Registry.
The Registry API provides several routes to access the schema information:
- Subject overview (subject = topic + '-value'): `http://localhost:8081/subjects/`
- Subject details: `http://localhost:8081/subjects/count-value/versions/1`

However, `1p_multiples.py` does not use the `CKafkaPC.py` class and produces schema-less data, to represent legacy sources.
The third program, started via `docker-compose_2c_print.yml`, receives the messages from the broker and prints them.
The output from `1p_count_up.py` is a key-value pair, as defined in the schema.
The output from `1p_multiples.py` is the raw value.
Even though the data from legacy sources can be received without a schema, it is not possible to use a producer to send the data without a schema to the broker.
This enforces the use of schemas for well-defined interfaces.
The publishing program then exits with code 0, because it successfully sent all its messages.
The receiving program waits for further messages until the time-out is reached.
You can stop the receiving program and the Kafka Container with `Ctrl-C`.
After the containers stopped you can execute the following command to remove the containers:\
`docker-compose -f docker-compose_1p.yml down`\
`docker-compose -f docker-compose_2c_print.yml down`\
`docker-compose -f docker-compose_kafka.yml down`

A lot of things happened in the background to make this work:
+ Docker-compose builds the Containers from the Dockerfiles in `src`.
+ The Dockerfiles specify the base image, install the requirements found in `./src/configurations/requirements.txt`, copy the sources into the container and set the program to execute when the container starts.
+ The Docker-compose files also specify the environment for the container and set the URL for the Kafka broker, the incoming / outgoing topics for our modules and also the serialization schema.
+ Avro serializes the messages according to `./src/schema/count.avsc` and `./src/schema/multiples.avsc`.
Messages that do not comply to this schema raise an error and can´t be send.
