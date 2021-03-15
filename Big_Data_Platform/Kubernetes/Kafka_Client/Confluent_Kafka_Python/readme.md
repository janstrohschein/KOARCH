# Confluent Kafka Python Client


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


