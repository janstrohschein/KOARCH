#  Knowledge Module
The knowledge module stores information about the use case and knowledge about the available algorithms.

FastAPI is used to implement APIs according to the [OpenAPI specification](http://spec.openapis.org/oas/v3.0.3).
The framework enables a quick and easy implementation and automatically generates a web interface based on the API specification.

# Example
The example container starts a FastAPI service and provides the use case information and algorithm knowledge.

## Preparation
Please install Docker and docker-compose to run the containers.
Instructions can be found [here](https://github.com/janstrohschein/KOARCH/tree/master/Big_Data_Platform/Docker).

Before starting the container we create a network, for easier communication between containers, by running this command in a terminal:\
`docker network create caai`

To launch the example please execute the following command in a terminal:\
`docker-compose up`

## Access the Webinterface
The FastAPI provides a web interface based on the API description, which can be accessed in a browser at:
`http://localhost:8001/docs` or
`http://127.0.0.1:8001/docs`

All routes and functions defined in knowledge.py are accessible via the web interface:
- (GET) Returns the use case information: `/use_case/`\
  No Parameters
- (PUT) Updates the use case information: `/use_case/`\
  Parameters:\
  use_case (str), goal (str), feature (str)
- (GET) Returns the complete knowledgebase: `/knowledge/`\
  No Parameters
- (GET) Filters the knowledge for a specific use case: `/knowledge/usecase/`\
  Parameters:\
  use_case (str)
- (GET) Filters the knowledge for a specific algorithm: `/knowledge/algorithm/`\
  Parameters:\
  use_case (str), goal (str), feature (str), algorithm (str)
- (GET) Filters the knowledge and returns feasible pipelines: `/knowledge/feasible_pipelines/`\
  Parameters:\
  use_case (str), goal (str), feature (str)
- (PUT) Imports a YAML file as new knowledgebase: `/import_knowledge/`\
  No Parameters\
  Request Body Required:\
  file (multipart/form-data)
- (GET) Exports the current content of the knowledgebase into a YAML file: `/export_knowledge/`\
  No Parameters


## Shutdown Docker Containers
- Stop the container with:\
  `ctrl + c`
- Remove the container with:\
  `docker-compose down`

## Technical Details
- The implementation of the knowledge API can be found in `./src/knowledge.py`.
- The module initializes the knowledgebase with the content of `./src/data/knowledge.yaml`.
- Docker-compose (`docker-compose.yml`) uses the instructions from `./src/Dockerfile` to build the container.
- The Dockerfile uses a base image and installs the required packages as specified in `./src/configurations/requirements.txt`.
