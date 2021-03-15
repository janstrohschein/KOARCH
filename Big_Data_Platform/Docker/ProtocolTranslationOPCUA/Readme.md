# Protocol Translation with OPC UA
This is an example of a protocol translation that reads values from an OPC UA server and sends it as a message via Kafka with a schema. Furthermore, a consumer is implemented that enables to change values on the OPC UA server via Kafka messages. Due to implementation issues, the adaption is implemented without a schema.

## Requirements
Before you run the software, please check the following requirements
1. Docker and docker-compose have to be installed to run the containers. Instructions can be found [here](https://github.com/janstrohschein/KOARCH/tree/master/Big_Data_Platform/Docker).

2. A broker with a schema registry has to run, you can use [this](https://github.com/janstrohschein/KOARCH/tree/master/Big_Data_Platform/Docker/Kafka_Client/Confluent_Kafka_Python).

3. An OPC UA server has to be run on your system. The examples use the [OPC UA ANSI C Demo Server](https://www.unified-automation.com/downloads/opc-ua-servers.html) from Unified Automation. You can download it for free, but you have to register yourself at the website. You can also use a different server, but you have to change the node IDs and the address.

4. The .NET Core 3.1 Framework was used to create the software, which you can find [here](https://dotnet.microsoft.com/download/dotnet). There might be compatibility issues with other versions. 


## Example
At first start the Kafka broker and the OPC UA server (see Requirements). Open the console, navigate to the folder where the docker-compose file is in and enter the command `docker-compose -f docker-compose_opc.yml up --build`. The docker image will be built and executed.
If it is successful, you should see the OPC UA URL, the connection status, the nodes and their values as well as the messages that are sent by the producer. Finally, a test message is produced that triggers the writing of a new value to the OPC server. The message is hardcoded and changes the node Demo.SimulationSpeed to 20. You can check and set the values on the server manually with the [UA Expert](https://www.unified-automation.com/downloads/opc-ua-clients.html) from Unified Automation. As well as for the server, you have to register for free. Finally, you can terminate the container with `ctrl + c`.
You can remove the container by `docker-compose -f docker-compose_opc.yml down` and start it again without a build using `docker-compose -f docker-compose_opc.yml up`.

If you do not want to use docker-compose, you can alternatively open the console, navigate to the folder of the Dockerfile and enter the command
`docker build -t opcgateway .` to build the container. That might take a few minutes. If the building process was successfully finished, you start the container with `docker run --network="caai" opcgateway`.

## Explanation of the Function
The program reads in the section 0p_opc in the `config.yml` and adapts the OPC UA connection regarding this. So you can change the Address of the OPC UA server as well as the notes that are requested and the polling interval. So, the data is acquired by polling the notes. The LibUA library also supports subscription, if it is needed, see [example](https://github.com/nauful/LibUA/blob/master/NET%20Core/TestClient/Program.cs). 

The Kafka configuration is done in the program itself and not read from the `config.yml`. However, two schemas are defined, even so only the `CPPSdataGeneric.avsc` is used. It provides a list of nodes and their values. This has two advantages: (i) it is generic and this one schema can be used for versatile applications and (ii) the node ID can be properly represented, because no special characters are allowed in avro schemas.
As mentioned above the consumer is running without a schema until now.

The values of the node are acquired 10 times before the test message for the adaption is send. The data acquired via OPC UA is sent on the topic `CPPSdata`.
The consumer for the adaption listens to the topic `CPPSadaption` and is in the format `<nodeID>:<value>`. 