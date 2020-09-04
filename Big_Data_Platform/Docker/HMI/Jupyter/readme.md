# Jupyter
The [Jupyter Notebook](https://jupyter.org/) is an open-source web application that allows you to create and share documents that contain live code, equations, visualizations and narrative text. Uses include: data cleaning and transformation, numerical simulation, statistical modeling, data visualization, machine learning, and much more.

# Example
The datascience notebook used for this example includes libraries for data analysis from the Julia, Python, and R communities. 
This example has the following functionality:
- Uses the `docker-compose.yml` to build a Jupyter notebook container.
- Mounts the `./src/notebooks/` folder in the Jupyter container to use notebooks from the host system.
- Sets up port forwarding between the host system and the container to access the web interface via browser.
- Connects the Jupyter to the same Docker network as the other CAAI containers to allow access to all resources via Jupyter notebooks.

## Preparation
Please install Docker and docker-compose to run the containers.
Instructions can be found [here](https://github.com/janstrohschein/KOARCH/tree/master/Big_Data_Platform/Docker).

Please make sure that your Docker Settings allow to share the local filesystem with the container to create a persistent volume.
Since Docker 2.20 this has to be enabled manually, the instructions can be found [here](https://stackoverflow.com/questions/60754297/docker-compose-failed-to-build-filesharing-has-been-cancelled).

Before starting the container we create a network, for easier communication between containers, by running this command in a terminal:\
`docker network create caai`

To launch the example please execute the following command in the terminal:\
`docker-compose up`

## Access the Webinterface
The Jupyter service provides a webinterface can be accessed in a browser at:
`http://localhost:8888`
The webinterface shows a list of currently available notebooks.
The user is able to create a new notebook with customized analysis or run an existing notebook.
There is one sample notebook provided through the `./src/notebooks/` folder with a Python introduction.
This notebook can be opened and all cells can be executed individually. 

## Shutdown Docker Containers
Stop and remove Jupyter container:\
    `docker-compose down`
