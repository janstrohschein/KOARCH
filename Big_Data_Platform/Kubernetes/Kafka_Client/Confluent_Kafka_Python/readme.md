# Confluent Kafka Python Client 
The base image for the Python Kafka client is used for all containers and can be found on the [KOARCH Docker Hub](https://hub.docker.com/repository/docker/koarch/confluent_kafka_python).

The example consists of several steps to send and receive messages on the Kubernetes cluster:
- create ConfigMaps on the cluster to configure the containers
- instantiate the 2 producers and 1 consumer with the additional configuration

## Embed yaml files in ConfigMaps
- create ConfigMaps from files on host:  
    - `kubectl create configmap general --from-file=general_config.yml`  
    - `kubectl create configmap 1p-count-up --from-file=1p_count_up_config.yml`
    - `kubectl create configmap 1p-multiples --from-file=1p_multiples_config.yml`
    - `kubectl create configmap 2c-print --from-file=2c_print_config.yml`
- verify the successful creation of the ConfigMaps:  
    `kubectl describe cm general`  
    ```yml
    Name:         general
    Namespace:    default
    Labels:       <none>
    Annotations:  <none>

    Data
    ====
    general_config.yml:
    ----
    KAFKA_BROKER_URL: kafka-all-broker:29092
    KAFKA_CONSUMER_TIMEOUT_MS: 120000
    KAFKA_SCHEMA_REGISTRY_URL: karapace-registry-service:80
    Events:  <none>
    ```

## Create the example containers
The pod specification can be found in `caai_count_example.yml`. Please instruct Kubernetes to instantiate the 3 pods via:

- `kubectl apply -f caai_count_example.yml`

Verify the pod creation via:  
- `kubectl get pods`

Inspect the logs via:  
- `kubectl logs 2c-print`

The output should look as follows:  
```
start 2c_print
created KafkaPC
Received on topic 'multiples': {'multiple': 0}
Received on topic 'multiples': {'multiple': 1}
Received on topic 'multiples': {'multiple': 4}
Received on topic 'count': {'count': 0}
Received on topic 'count': {'count': 1}
Received on topic 'count': {'count': 2}
Received on topic 'count': {'count': 3}
Received on topic 'count': {'count': 4}
Received on topic 'count': {'count': 5}
Received on topic 'count': {'count': 6}
Received on topic 'count': {'count': 7}
Received on topic 'count': {'count': 8}
Received on topic 'count': {'count': 9}
Received on topic 'multiples': {'multiple': 9}
Received on topic 'multiples': {'multiple': 16}
Received on topic 'multiples': {'multiple': 25}
Received on topic 'multiples': {'multiple': 36}
Received on topic 'multiples': {'multiple': 49}
Received on topic 'multiples': {'multiple': 64}
Received on topic 'multiples': {'multiple': 81}
```

## Stop the example
Execute the following commands to remove the pods and the ConfigMaps:

- `kubectl delete -f caai_count_example.yml`
- `kubectl delete cm general`
- `kubectl delete cm 1p-count-up`
- `kubectl delete cm 1p-multiples`
- `kubectl delete cm 2c-print`
