# FastAPI
FastAPI is used to implement APIs according to the [OpenAPI specification](http://spec.openapis.org/oas/v3.0.3).
The framework enables a quick and easy implementation and automatically generates a Human-Machine-Interface (HMI) based on the API specification.

# Preparation
Please install Docker and docker-compose to run the containers.
Instructions can be found [here](https://github.com/janstrohschein/KOARCH/tree/master/Big_Data_Platform/Docker).

Before we start the Kafka broker we create a network, for easier communication between containers, by running this command in a terminal:
`docker network create caai`

Now you can launch the Kafka broker with the following command:\
`docker-compose -f docker-compose_kafka.yml up`

# Example
The example consists of 4 modules:
- L1_P_count & L1_P_double_count\
  Produce simple messages and publish those to seperate topics via Kafka.
- L2_C_Reporting\
  Collects the messages from all specified topics and sends the messages to different API endpoints with optional processing.
- L3_API_HMI\
  Dynamically creates endpoints based on the configuration.  

To launch the example please open another terminal and execute the following command:
`docker-compose up`

## Collecting information from several topics

The code snippet below is content of `./src/configurations/config.yml`.
It instructs the reporting module to collect the messages from the IN_TOPICs `AB_counts` and `AB_double_counts`. 
Those messages can be processed further or just forwarded to the destination API endpoint. Both is specified in `API_OUT` and can be extended easily.
```
2_c_reporting:
  IN_TOPIC:
    AB_counts: ./schema/count.avsc
    AB_double_counts: ./schema/count.avsc
  IN_GROUP: reporting
  API_OUT:
    AB_counts: forward_topic 
    AB_double_counts: forward_topic
  API_URL: http://3_API_HMI:8000
  API_ENDPOINT: /topic/
```
## Access the Webinterface
The FastAPI provides a webinterface based on the API description.
The HMI can be accessed in a browser at:
`http://localhost:8001/docs`

All routes and functions defined in L3_API_HMI.py are accessible via the HMI:
- (GET) Return all results via: `/topics/`
- (GET) Return results for a specific topic via: `/topic/{topic_name}/`
- (GET) Export the results for a specific topic to CSV via: `/topic_csv/{topic_name}/`
- (POST) Add a row to a specific topic via: `/topic/{topic_name}/`

The interface also shows the equivalent curl request, so the query can be translated into code.


# Shutdown Docker Containers
- Stop Kafka Containers\
    `docker-compose -f docker-compose_kafka.yml down`
- Stop other Containers and DB\
    `docker-compose down`
