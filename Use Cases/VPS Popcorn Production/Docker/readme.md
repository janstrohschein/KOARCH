# VPS Popcorn Production Use Case
We use the versatile production system (VPS), which is located in the SmartFactoryOWL, for evaluation of the cognitive component.
The VPS is a modular production system, which processes corn to produce popcorn which is used as packaging material.
Due to its modularity, it can be adapted to the current order easily. 
Efficiently operating the VPS is a challenge because of many parameters influence the result, which cannot be measured inline, e.g., the moisture of the corn.
Thus, a data-driven optimization is a promising method to increase efficiency, which is performed using the CAAI and the introduced cognitive component.

The amount of corn that is filled into the reactor has to be optimized, to get the required amount of popcorn.
The overage of popcorn produced in one batch, or not fully filled boxes cannot be used, so it is waste.
The optimum is a trade-off between three minimization functions: the energy consumption ($f_1$), the processing time ($f_2$), and the amount of corn needed for a small box ($f_3$).
These functions are conflicting to some degree. 
The result of the optimization is a parameter value $x$ for the dosing unit that indicated the runtime of the conveyer and thus influence the amount of corn.
As the given optimization problem can be regarded as relatively simple, we will apply a single objective optimization algorithm and compute a weighted sum of the objectives.
This results in the following optimization problem:
<img src="./docs/optimization_formula.svg" width="400px">

The scalar weights of the corresponding objectives, $w_i$,  are chosen based on user's preferences. 
As a default, equal weights are used.
More details about the use case can be found in [our pre-print](https://arxiv.org/abs/2003.00925). 

Next we would like to present the implementation of our CAAI architecture for this use case.
All modules are implemented as Docker Containers and communicate via Kafka.


# Preparation 
Please install Docker and docker-compose to run the containers.
You find instructions for the Docker installation on their [website](https://docs.docker.com/get-docker/). 
To test the Docker installation you can open a terminal and execute `docker run hello-world`.

On some OS the Docker installation does not include docker-compose. You can find information for the installation [here](https://docs.docker.com/compose/install/)  in case you get a message that docker-compose is missing.

Before we start the Kafka broker we create a network, for easier communication between containers, by running this command in a terminal:
`docker network create caai`

Now you can start the Kafka broker with the following command:\
`docker-compose -f docker-compose_kafka.yml up`

# Run the experiment

The workflow is described in the figure below:

<img src="./docs/vps_use_case_workflow.jpg" width="800px">

A lot of things happened in the background to make this work:
+ Docker-compose builds the Containers from the Dockerfiles in `src`.
+ The Dockerfiles specify the base image, install the requirements found in `./src/configurations/requirements.txt`, copy the sources into the container and set the program to execute when the container starts.
+ The Docker-compose files also specify the environment for the container and set the URL for the Kafka broker, the incoming / outgoing topics for our modules and also the serialization schema.
+ Avro serializes the messages according to schemas defined in `./src/schema/`.
Messages that do not comply to the specified schema raise an error and can´t be send.

