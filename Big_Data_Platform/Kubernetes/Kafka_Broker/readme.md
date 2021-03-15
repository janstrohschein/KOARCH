# Install Kafka on Kubernetes
The Kafka installation on Kubernetes requires several steps.

## Cert-Manager
First, install cert-manager via:
- `kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v0.15.1/cert-manager.yaml`

## Zookeeper
Then install Zookeeper to manage the Kafka Cluster state ([see](https://github.com/pravega/zookeeper-operator)).

- `kubectl apply -f zookeeper_preparation.yaml`
- `kubectl apply -f zookeeper.yaml`

Verify the succesful creation of the Zookeeper pod via:
- `kubectl get pod zookeeper-0`  
The desired output looks as follows: 
```
NAME          READY   STATUS    RESTARTS   AGE
zookeeper-0   1/1     Running   0          5s
```
For additional information the `get` can be replaced with a `describe`.

## Kafka
Next, install the Kafka operator with the following steps:
- change the directory:  
	`cd kafka-operator`
- use Helm to install the Kafka operator with customized parameters:
	```
	helm install kafka-operator-test . --set operator.image.repository=koarch/kafka-operator,operator.image.tag=0.11.2,prometheusMetrics.enabled=false,prometheusMetrics.authProxy.enabled=false,rbac.enabled=true,alertManager.enable=false --namespace=default
	```

- the output will look similar to this:  
  ```
  NAME: kafka-operator-test
  LAST DEPLOYED: Mon Mar 15 16:37:44 2021
  NAMESPACE: default
  STATUS: deployed
  REVISION: 1
  TEST SUITE: None
  ```

- leave the subdirectory

The operator provides the custom Kubernetes resources for Kafka.
Now we can start the actual Kafka broker via:  
- `kubectl apply -f kafka.yaml`

The Kafka Broker will add random ID to the pod, as the deployment observes the Broker and creates new instances, if necessary. Thus, you can verify the creation of the Kafka Broker via: 
- `kubectl get pods`

The output will show 2 Broker instances after a short while.

## Karapace Avro Schema Registry 
Karapace is a drop-in replacement for the Confluent Schema Registry [Website](https://github.com/aiven/karapace).


Install Karapace via:  
- `kubectl apply -f https://raw.githubusercontent.com/janstrohschein/KOARCH/master/Big_Data_Platform/Kubernetes/Karapace/karapace.yaml`

Verify successful installation by calling the API from your Browser:
- `http://localhost:8080/karapace`

The resulting `{}` indicates an empty registry.

Now we can use the Kafka Broker to send and receive messages in Kubernetes. Please find an example [here](/Big_Data_Platform/Kubernetes/Kafka_Client/Confluent_Kafka_Python/readme.md).



# Un-install

## Karapace Avro Schema Registry
Remove Karapace from the Kubernetes Cluster with the following command: 
- `kubectl delete -f https://raw.githubusercontent.com/janstrohschein/KOARCH/master/Big_Data_Platform/Kubernetes/Karapace/karapace.yaml`  

Please note that stopping and removing Karapace or any other software can take a few seconds.


## Kafka
Remove the Kafka Broker from the Kubernetes Cluster via:  
- `kubectl delete -f kafka.yaml`  

Change into the kafka-operator directory and use Helm to uninstall the Kafka resources 
- `helm uninstall kafka-operator-test`  

Please leave the subdirectory after Helm finishes.
## Zookeeper
Stop and remove Zookeeper with the following command:
- `kubectl delete -f zookeeper.yaml`

Remove the additional Zookeeper resources via:
- `kubectl delete -f zookeeper_preparation.yaml`


## Cert-Manager
Remove Cert-Manager via the command:
- `kubectl delete -f https://github.com/jetstack/cert-manager/releases/download/v0.15.1/cert-manager.yaml`
