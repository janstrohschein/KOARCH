# Big Data Platform on Kubernetes


# Installation
Running the Big Data Platform requires several tools:
- Docker: Docker provides a container engine to run virtualized containers on the host system.
- k3s/k3d: k3s is a minimal Kubernetes distribution. k3d is used to set-up k3s in Docker containers.
- kubectl: kubectl is an application to interact with the Kubernetes cluster.
- Helm: A package manager for Kubernetes. 

## Docker
Please install Docker and docker-compose to run the containers.
You find instructions for the Docker installation on their [website](https://docs.docker.com/get-docker/). 
To test the Docker installation you can open a terminal and execute `docker run hello-world`.

On some OS the Docker installation does not include docker-compose. You can find information for the installation [here](https://docs.docker.com/compose/install/)  in case you get a message that docker-compose is missing.

## Other tools

### Windows
[ Chocolatey ](https://chocolatey.org/) is a package manager for Windows.
It makes the installation of the required tools extremely easy.
Follow the [instructions](https://chocolatey.org/install) to install choco on your system.
Type `choco` in a terminal to verify the successful installation.
Now it is possible to install the other tools via:  
`choco install k3d kubernetes-cli kubernetes-helm`  
Verify the successful installation of the tools:  
`choco list -localonly`

It is also possible to install the tools without Chocolatey. Please follow the individual installation instructions if you prefer the manual installation:
- [k3d](https://github.com/rancher/k3d#get)
- [kubectl](https://kubernetes.io/de/docs/tasks/tools/install-kubectl/)
- [helm](https://helm.sh/docs/intro/install/)

### Ubuntu

#### k3s
Ubuntu needs to use the legacy iptables for successful k3s installation ([see](https://wiki.debian.org/nftables#Current_status)).
- `update-alternatives --set iptables /usr/sbin/iptables-legacy`
- `update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy`

In case you want to run Kubernetes on a Raspberry Pi additional settings for the kernel are required.
Ubuntu stores the settings in `/boot/firmware/`.
- `sudo nano /boot/firmware/cmdline.txt`
- append `cgroup_memory=1 cgroup_enable=memory`

Install k3d to create a k3s cluster via Docker ([see](https://github.com/rancher/k3d#get)).  
- `wget -q -O - https://raw.githubusercontent.com/rancher/k3d/main/install.sh | TAG=v4.0.0 bash`  

#### Kubectl
Kubectl allows to interact with the Kubernetes cluster.
Installation instructions for kubectl can be found [here](https://kubernetes.io/docs/tasks/tools/install-kubectl/).
The following commands install the tool via the Ubuntu package manager: 
- `sudo apt-get update && sudo apt-get install -y apt-transport-https gnupg2 curl`
- `curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -`
- `echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list`
- `sudo apt-get update`
- `sudo apt-get install -y kubectl`

#### Helm
Detailed installation instructions for Helm can be found [here](https://helm.sh/docs/intro/install/).
The shortest installation on Linux can be done via:
- `curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash`

# Cluster Setup

Create a new cluster with name 'dev', consisting of one server and a loadbalancer.
- `k3d cluster create dev --port 8080:80@loadbalancer --port 8443:443@loadbalancer`

K3d provides the following commands to control the cluster after creation:  
Stop the cluster: `k3d cluster stop <clustername>`  
Start the cluster: `k3d cluster start <clustername>`  
Delete the cluster: `k3d cluster delete <clustername>`

Now it is possible to use kubectl to deploy a first example application.
Make sure that kubectl works on the k3s cluster by providing the k3s context.
- `kubectl config use-context k3d-<clustername>`

Confirm that the cluster access works.  
List the cluster nodes:
- `kubectl get nodes`

Show additional cluster information:
- `kubectl cluster-info`

## Deploy an example application
Deploy an nginx example application to test the cluster accessibility.
Kubernetes can receive instructions either directly via the command line or via `.yml` file for more complex cases.  

Create a nginx Deployment, which instructs the Kubernetes scheduler to create a nginx pod and observes its availability. 
In case of pod failure, the Deployment will create new pods.  
- `kubectl create deployment nginx --image=nginx`  

Create a Service to map the service port 80 to the application port 80.  
- `kubectl create service clusterip nginx --tcp=80:80`  

Create an Ingress via `.yml` file to make the application available via the loadbalancer for outside access:  
- `kubectl apply -f https://raw.githubusercontent.com/janstrohschein/KOARCH/master/Big_Data_Platform/Kubernetes/example_ingress.yml`

Display the Kubernetes objects with the following commands:
- `kubectl get deployment nginx`
- `kubectl get service nginx`
- `kubectl get ingress nginx`

Change "get" to "describe" to see more details on each object.
The nginx application is now accessible via the webbrowser at `localhost:8080/test`.

Remove the application and associated Kubernets objects with the following commands:
- `kubectl delete ingress nginx`
- `kubectl delete service nginx`
- `kubectl delete deployment nginx`

Kubernetes will then instruct the scheduler to remove the example application.
Shortly after, the access via the browser will no longer work. 
Use the same commands to verify that each object got removed:
- `kubectl get deployment nginx`
- `kubectl get service nginx`
- `kubectl get ingress nginx`

