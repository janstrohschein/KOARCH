from dataclasses import dataclass, field
from typing import List

import kubernetes as k8s
from pint import UnitRegistry
from pint.quantity import Quantity


@dataclass
class NodeInstance:
    node_name: str
    cpu_alloc: Quantity
    mem_alloc: Quantity
    cpu_usage: Quantity
    mem_usage: Quantity
    cpu_perc: int
    mem_perc: int


@dataclass
class ClusterInfo:
    nodes: List[NodeInstance] = field(default_factory=list)

    def get_cpu_allocatable_sum(self):
        return sum(node.cpu_alloc for node in self.nodes)

    def get_mem_allocatable_sum(self):
        return sum(node.mem_alloc for node in self.nodes)

    def get_cpu_usage_sum(self):
        return sum(node.cpu_usage for node in self.nodes)

    def get_mem_usage_sum(self):
        return sum(node.mem_usage for node in self.nodes)

    def get_cpu_usage_perc_avg(self):
        cpu_alloc = self.get_cpu_allocatable_sum()
        cpu_usage = self.get_cpu_usage_sum()
        result = 0
        try:
            result = int(cpu_usage / cpu_alloc * 100)
        except ZeroDivisionError as e:
            print(f"Could not divide by 0. Error: {repr(e)}")

        return result

    def get_mem_usage_perc_avg(self):
        mem_alloc = self.get_mem_allocatable_sum()
        mem_usage = self.get_mem_usage_sum()
        result = 0
        try:
            result = int(mem_usage / mem_alloc * 100)
        except ZeroDivisionError as e:
            print(f"Could not divide by 0. Error: {repr(e)}")

        return result


@dataclass
class ContainerInstance:
    container_name: str
    pod_name: str
    cpu_usage: Quantity
    mem_usage: Quantity
    cpu_perc: int
    mem_perc: int


@dataclass
class ContainerInfo:
    container_name: str
    containers: List[ContainerInstance] = field(default_factory=list)

    def get_cpu_sum(self):
        return sum(container.cpu_usage for container in self.containers)

    def get_mem_sum(self):
        return sum(container.mem_usage for container in self.containers)

    def get_cpu_perc_sum(self):
        return sum(container.cpu_perc for container in self.containers)

    def get_mem_perc_sum(self):
        return sum(container.mem_perc for container in self.containers)


class KubeAPI:
    def __init__(self):
        super(KubeAPI, self).__init__()
        self.unit_definitions_file = "C:/Users/stroh/Programming/GitHub/KOARCH/Big_Data_Platform/Kubernetes/Cognition/example/src/kubernetes_units.txt"
        self.kube_local_config = "C:/Users/stroh/.kube/config"
        self.core_api = None
        self.custom_api = None
        self.init_unit_registry()

    def init_unit_registry(self):
        """The Pint Unit Registry contains the definitions for the conversion of Kubernetes CPU or RAM units.
        The definition file is used as input and describes the relationships between units.
        Initializes self.q() that can be used for any Quantity of Kubernetes CPU or RAM in the program.
        """
        ureg = UnitRegistry()
        try:
            ureg.load_definitions(self.unit_definitions_file)
        except Exception as e:
            print(f"Error loading quantity definitions: {repr(e)}")

        self.q = ureg.Quantity

    def init_kube_connection(self):
        """Initializes a connection to the Kubernetes CoreV1Api and CustomObjectsApi.
        Tries to use the incluster config first and afterwards local config if KubeAPI is used in local development.
        Adjust self.kube_local_config as necessary.
        """
        try:
            k8s.config.load_incluster_config()
        except Exception as e:
            print(f"Error loading incluster config: {repr(e)}, trying to load local config instead")
            k8s.config.load_kube_config(self.kube_local_config)

        self.core_api = k8s.client.CoreV1Api()
        self.custom_api = k8s.client.CustomObjectsApi()

    def get_perc_from_quant(self, n1: Quantity, n2: Quantity) -> int:
        """ The function transforms Pint quantities into a percentage.
        Pint is used for the conversion of different Kubernetes units for CPU and RAM.
        See: https://pint.readthedocs.io/en/stable/

        Args:
            n1 (Quantity)
            n2 (Quantity)

        Returns:
            [int]: Percentage value
        """
        result = 0
        try:
            result = int(n1 / n2 * 100)
        except ZeroDivisionError as e:
            print(f"Could not divide by 0. Error: {repr(e)}")

        return result

    def get_cluster_metrics(self) -> ClusterInfo:
        """Collects allocatable CPU/RAM as absolute numbers and used CPU/RAM as absolute numbers and percentage for each Node in the Cluster.

        Returns:
            ClusterInfo: ClusterInfo()
        """
        if self.custom_api is None:
            print("Connect to Kube Custom API first")
            exit

        node_data = self.custom_api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "nodes")
        cluster_alloc = self.get_cluster_allocatable()

        res = ClusterInfo()
        for node in node_data['items']:
            name = node['metadata']['name']
            cpu_alloc = cluster_alloc[name]['cpu']
            mem_alloc = cluster_alloc[name]['mem']
            cpu_usage = self.q(node['usage']['cpu'])
            mem_usage = self.q(node['usage']['memory'])
            cpu_perc = self.get_perc_from_quant(cpu_usage, cpu_alloc)
            mem_perc = self.get_perc_from_quant(mem_usage, mem_alloc)
            node_info = NodeInstance(node_name=name,
                                     cpu_alloc=cpu_alloc,
                                     mem_alloc=mem_alloc,
                                     cpu_usage=cpu_usage,
                                     mem_usage=mem_usage,
                                     cpu_perc=cpu_perc,
                                     mem_perc=mem_perc)
            res.nodes.append(node_info)

        return res

    def get_pod_metrics(self) -> dict(ContainerInfo):
        """Collects the pod metrics and groups them by Containername to aggregate
        usage data for containers that work with multiple instances.

        Returns:
            dict(ContainerInfo): Access metrics via Containername
        """
        if self.custom_api is None:
            print("Connect to Kube Custom API first")
            exit

        cluster_alloc = self.get_cluster_allocatable()

        pod_data = self.custom_api.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'pods')

        res = {}
        for pod in pod_data['items']:
            pod_name = pod['metadata']['name']
            for container in pod['containers']:
                name = container['name']
                if name not in res:
                    res[name] = ContainerInfo(container_name=name)
                cpu_usage = self.q(container['usage']['cpu'])
                mem_usage = self.q(container['usage']['memory'])
                cpu_perc = self.get_perc_from_quant(cpu_usage, cluster_alloc['sum_cpu'])
                mem_perc = self.get_perc_from_quant(mem_usage, cluster_alloc['sum_mem'])

                new_ci = ContainerInstance(pod_name=pod_name,
                                           container_name=name,
                                           cpu_usage=cpu_usage,
                                           mem_usage=mem_usage,
                                           cpu_perc=cpu_perc,
                                           mem_perc=mem_perc)
                res[name].containers.append(new_ci)
                # print(f"Container {name} uses CPU: {cpu_usage} ({cpu_per}%), Memory: {mem_usage} ({mem_per}%)")

        return res

    def get_cluster_allocatable(self) -> dict:
        """Collects allocatable CPU and RAM for each Kubernetes Node and aggregates the data for the Cluster.

        Returns:
            dict: Contains the aggregated data as 'sum_cpu' and 'sum_mem' and also data for each node via 'node_name'
        """
        if self.core_api is None:
            print("Connect to Kube Core API first")
            exit

        node_data = {}
        node_data['sum_cpu'] = 0
        node_data['sum_mem'] = 0

        for node in self.core_api.list_node().items:
            alloc = node.status.allocatable
            alloc_dict = {'cpu': self.q(alloc['cpu']),
                          'mem': self.q(alloc['memory'])}
            node_data[node.metadata.name] = alloc_dict
            node_data['sum_cpu'] += alloc_dict['cpu']
            node_data['sum_mem'] += alloc_dict['mem']

        return node_data
