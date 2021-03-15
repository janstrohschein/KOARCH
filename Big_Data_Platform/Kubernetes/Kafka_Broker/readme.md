# Install Kafka on Kubernetes
The Kafka installation on Kubernetes requires several steps.
First, install cert-manager via:
- `kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v0.15.1/cert-manager.yaml`

Then install Zookeeper to manage the Kafka Cluster state ([see](https://github.com/pravega/zookeeper-operator)).

- `kubectl apply -f zookeeper_preparation.yaml`
- `kubectl apply -f zookeeper.yaml`

Install the Kafka operator with the following steps:
- change the directory:
	`cd kafka-operator`
- use Helm to install the Kafka operator with customized parameters:
	```
	helm install kafka-operator-test . --set operator.image.repository=koarch/kafka-operator,operator.image.tag=0.11.2,prometheusMetrics.enabled=false,prometheusMetrics.authProxy.enabled=false,rbac.enabled=true,alertManager.enable=false --namespace=default
	```
- leave the subdirectory

The operator provides the custom Kubernetes resources for Kafka.
Now we can start the actual Kafka broker via:
`kubectl apply -f kafka.yaml`

# Install Karapace Avro Schema Registry 
Karapace is a drop-in replacement for the Confluent Schema Registry [Website](https://github.com/aiven/karapace).


Install via:  
- `cd /home/ubuntu/kubernetes/karapace`  
- `kubectl apply -f karapace.yml`

Verify successful installation via: 

- `kubectl run curl --image=nerzhul/curl-arm64 -it --rm`  
- `nslookup karapace-registry-service`
- `curl -X GET karapace-registry-service:80`

The resulting `{}` indicates an empty registry.

