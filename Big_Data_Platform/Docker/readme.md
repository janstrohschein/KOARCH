# Big Data Platform in Docker
The components of the big data platform are various software building blocks, each implemented in a Docker container.
Modules do not communicate directly with each other, but use messaging to publish and subscribe to relevant topics.

# Docker Installation
Please install Docker and docker-compose to run the containers.
You find instructions for the Docker installation on their [website](https://docs.docker.com/get-docker/). 
To test the Docker installation you can open a terminal and execute `docker run hello-world`.

On some OS the Docker installation does not include docker-compose. You can find information for the installation [here](https://docs.docker.com/compose/install/)  in case you get a message that docker-compose is missing.

# Building blocks
The subfolders contain the different building blocks of the Big Data Platform. 
- Cognition
- DB
- HMI
- [Kafka](Kafka/readme.md)\
All modules rely on the messaging ability for indirect communication with other modules.
Thus the Kafka building block is the base class for most other modules and more specialized blocks like a connector to PostgresDB inherit the additional Kafka functionality.
- [Knowledge](Knowledge/readme.md)
The knowledge module is implemented as an API to store, modify and retrieve the knowledge at any time.
