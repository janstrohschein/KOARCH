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
- [Cognition](Cognition/readme.md)
- DB
  - [Postgres](DB/Postgres/readme.md)\
  The relational database stores structured data. 
- HMI
  - [FastAPI](HMI/FastAPI/readme.md)\
  Provides access to data for humans and other systems based on the OpenAPI specification.
  - [Jupyter](HMI/Jupyter/readme.md)
  The Jupyter datascience notebook includes libraries for data analysis in Julia, Python and R.
- [Kafka](Kafka/readme.md)\
All modules rely on the messaging ability for indirect communication with other modules.
Thus the Kafka building block is the base class for most other modules and more specialized blocks like a connector to PostgresDB inherit the additional Kafka functionality.
- [Knowledge](Knowledge/readme.md)\
The knowledge module is implemented as an API to store, modify and retrieve the knowledge at any time.

# General Docker Structure
The different building blocks or use cases are implemented as Docker containers.
Several containers are managed together via docker-compose files.
The following structure shows all the possible different parts:

```
Building Block
|- docs
|- src
  |-- classes
  |-- configurations
  |-- schema
  | something.py
  | Dockerfile_something
| docker-compose.yml
| docker-compose_kafka.yml
| readme.md
```

## |- docs
Contains images, diagrams and other supporting material for the documentation.
## |- src
The source folder stores the code files as well as the Dockerfiles.
Dockerfiles consist of instructions to build a container. 
The Dockerfile is named after the module it containerizes. 
### |-- classes
The subfolder contains the different classes, e.g., the Kafka class, for other modules to inherit.
### |-- configurations
The configurations folder stores several files:
- the `config.yml` contains the configuration for all modules in the project. 
The relevant sections for each module are specified in the `docker-compose.yml`.
- the `requirements.txt` contains all the packages that need to be installed in a container. 
The Dockerfile copies the file into the container and installs the packages during the build process.
### |-- schema
The containers use indirect communication with a messaging approach.
All messages are verified with the related Avro schema, which is stored in an `.avsc` file.
Each module specifies its input- and output-topics and the associated schemas in the `config.yml`.
## |- docker-compose files
Several services are combined into a docker-compose file, which allows to manage all services together.
Each service entry consists of:
- the container and host name.
- build information such as the base image or the path to the Dockerfile.
- assign files or volumes from the host system to a specific path in the container file system.
- environment variables, e.g., the config path and the config sections relevant to the module. 
- port forwarding from the host system to the container.

Furthermore it is also possible to define a common network for all containers and to specify how Docker volumes should be used. 

## |- readme
The `readme.md` explains the module / use case and gives usage instructions. 
