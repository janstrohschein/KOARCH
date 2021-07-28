import string
import random
from dataclasses import dataclass, field
from typing import List, Dict

import kubernetes as k8s
from kubernetes.client.models.v1_volume import V1Volume
from kubernetes.client.models.v1_volume_mount import V1VolumeMount
from kubernetes.client.rest import ApiException
from kubernetes import client

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


@dataclass
class ConfigMap:
    """refers to a Kubernetes ConfigMap
    see: https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/

    create CM on Kubernetes from existing .yml-files via:
    kubectl create configmap <name> --from-file=<file_name>.yml

    The original filename is the key, the path is used to mount the original file in a container
    """

    name: str
    key: str
    path: str


@dataclass
class VolumeMount:
    name: str
    mount_path: str
    sub_path: str


@dataclass
class Job:
    name: str
    image: str
    cluster_name: str = field(init=False)
    version: str
    namespace: str = "default"
    env_vars: Dict = field(default_factory=dict)
    config_maps: List[ConfigMap] = field(default_factory=list)

    def id_generator(self, size=12, chars=string.ascii_lowercase + string.digits):
        return "".join(random.choice(chars) for _ in range(size))

    def __post_init__(self):
        self.cluster_name = f"{self.name.replace(' ', '-').lower()}-{self.id_generator()}"


@dataclass
class Deployment:
    name: str
    image: str
    cluster_name: str = field(init=False)
    version: str
    namespace: str = "default"
    env_vars: Dict = field(default_factory=dict)
    config_maps: List[ConfigMap] = field(default_factory=list)

    def id_generator(self, size=12, chars=string.ascii_lowercase + string.digits):
        return "".join(random.choice(chars) for _ in range(size))

    def __post_init__(self):
        self.cluster_name = f"{self.name.replace(' ', '-').lower()}-{self.id_generator()}"


class KubeAPI:
    def __init__(self):
        super(KubeAPI, self).__init__()
        self.unit_definitions_file = "/Big_Data_Platform/Kubernetes/Cognition/example/src/kubernetes_units.txt"
        # TODO remove local config after testing
        # self.kube_local_config = "C:/Users/stroh/.kube/config"
        self.kube_local_config = "/mnt/c/Users/stroh/.kube/config"
        self.container_config_path = "/etc/config/"
        self.core_api = None
        self.custom_api = None
        self.batch_api = None
        self.cpu_threshold = 60
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
            print(
                f"Error loading incluster config: {repr(e)}, trying to load local config instead")
            k8s.config.load_kube_config(self.kube_local_config)

        self.core_api = k8s.client.CoreV1Api()
        self.custom_api = k8s.client.CustomObjectsApi()
        self.batch_api = k8s.client.BatchV1Api()
        self.apps_api = k8s.client.AppsV1Api()

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
        if n1 == 0 or n2 == 0:
            return 0

        result = 0
        try:
            result = int(n1 / n2 * 100)
        except ZeroDivisionError as e:
            print(f"Could not divide by 0. Error: {repr(e)}")
        except Exception as e:
            print(f"Error: {repr(e)}")

        return result

    def get_cluster_metrics(self) -> ClusterInfo:
        """Collects allocatable CPU/RAM as absolute numbers and used CPU/RAM as absolute numbers and percentage
        for each Node in the Cluster.

        Returns:
            ClusterInfo: ClusterInfo()
        """
        if self.custom_api is None:
            print("Connect to Kube Custom API first")
            exit

        node_data = self.custom_api.list_cluster_custom_object(
            "metrics.k8s.io", "v1beta1", "nodes")
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

    def get_pod_metrics(self) -> Dict[str, ContainerInfo]:
        """Collects the pod metrics and groups them by Containername to aggregate
        usage data for containers that work with multiple instances.

        Returns:
            dict(ContainerInfo): Access metrics via Containername
        """
        if self.custom_api is None:
            print("Connect to Kube Custom API first")
            exit

        cluster_alloc = self.get_cluster_allocatable()

        pod_data = self.custom_api.list_cluster_custom_object(
            'metrics.k8s.io', 'v1beta1', 'pods')

        res = {}
        for pod in pod_data['items']:
            pod_name = pod['metadata']['name']
            for container in pod['containers']:
                name = container['name']
                if name not in res:
                    res[name] = ContainerInfo(container_name=name)
                cpu_usage = self.q(container['usage']['cpu'])
                mem_usage = self.q(container['usage']['memory'])
                cpu_perc = self.get_perc_from_quant(
                    cpu_usage, cluster_alloc['sum_cpu'])
                mem_perc = self.get_perc_from_quant(
                    mem_usage, cluster_alloc['sum_mem'])

                new_ci = ContainerInstance(pod_name=pod_name,
                                           container_name=name,
                                           cpu_usage=cpu_usage,
                                           mem_usage=mem_usage,
                                           cpu_perc=cpu_perc,
                                           mem_perc=mem_perc)
                res[name].containers.append(new_ci)
                # print(f"Container {name} uses CPU: {cpu_usage} ({cpu_per}%), Memory: {mem_usage} ({mem_per}%)")

        return res

    def get_job_metrics(self, namespace='default') -> Dict[str, ContainerInfo]:
        info = self.get_pod_metrics()

        jobs = self.batch_api.list_namespaced_job(namespace,
                                                  # include_uninitialized=False,
                                                  pretty=True,
                                                  timeout_seconds=60)

        target_list = [job.metadata.name for job in jobs.items]

        metric_res = {}

        for target in target_list:
            res = info.get(target)
            if res is not None:
                metric_res[target] = res

        return metric_res

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

    def has_capacity(self):
        res = False
        cluster_info = self.get_cluster_metrics()
        if cluster_info.get_cpu_usage_perc_avg() < self.cpu_threshold:
            res = True
        return res

    def get_vm_from_cm(self, cm: ConfigMap) -> VolumeMount:
        mount_path = self.container_config_path + cm.path

        return VolumeMount(name=cm.name, mount_path=mount_path, sub_path=cm.path)

    def create_volume_from_configmap(self, cms: List[ConfigMap]) -> List[V1Volume]:
        """add file in config map as volume in pod spec

        documentation:
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodSpec.md
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Volume.md
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1ConfigMapVolumeSource.md
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1KeyToPath.md

        template._template._spec.volumes

        V1PodSpec -> volumes=list[V1Volume]
            V1Volume -> name, config_map=V1ConfigMapVolumeSource
            V1ConfigMapVolumeSource -> name, items=list[V1KeyToPath]
                V1KeyToPath -> key, path

        source yaml:
        volumes:
        - name: general
        configMap:
            name: general
            items:
            - key: general_config.yml
                path: general.yml
        """
        volumes = []

        for cm in cms:

            # key = client.V1KeyToPath(key=cm.key, path=cm.path)
            # cmvs = client.V1ConfigMapVolumeSource(name=cm.name, items=[key])
            # volumes.append(client.V1Volume(name=cm.name, config_map=cmvs))

            key = client.V1KeyToPath(key=cm.key, path=cm.path)
            cmvs = client.V1ConfigMapVolumeSource(name=cm.name, items=[key])
            volume_name = cm.name + "-" + str(cm.key)
            volume_name = volume_name.split(".")[0]
            volumes.append(client.V1Volume(name=volume_name, config_map=cmvs))

        return volumes

    def create_volume_mount(self, cms: List[ConfigMap]) -> List[V1VolumeMount]:
        """add volume mount in template spec

        documentation:
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Container.md
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1VolumeMount.md

        template._template._spec._containers[0].volume_mounts

        V1Container -> volume_mounts=list[V1VolumeMount]
        V1VolumeMount -> name, mount_path, sub_path

        source yaml:

        volumeMounts:
        - name: general
            mountPath: /etc/config/general.yml
            subPath: general.yml
        - name: 1p-count-up
            mountPath: /etc/config/1p-count-up.yml
            subPath: 1p-count-up.yml
        """

        volume_mounts = []
        for cm in cms:
            # vm = self.get_vm_from_cm(cm)
            # v1vm = client.V1VolumeMount(
            #     name=vm.name, mount_path=vm.mount_path, sub_path=vm.sub_path
            # )
            # volume_mounts.append(v1vm)

            vm = self.get_vm_from_cm(cm)
            volume_name = cm.name + "-" + cm.key
            volume_name = volume_name.split(".")[0]
            v1vm = client.V1VolumeMount(name=volume_name,
                                        mount_path=vm.mount_path,
                                        sub_path=vm.sub_path)
            volume_mounts.append(v1vm)

        return volume_mounts

    def kube_create_job_object(self, job):
        """
        Create a k8 Job Object
        Minimum definition of a job object:
        {'api_version': None, - Str
        'kind': None,     - Str
        'metadata': None, - Metadata Object
        'spec': None,     -V1JobSpec
        'status': None}   - V1Job Status
        Docs: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Job.md
        # writing-a-job-spec
        Docs2: https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/

        V1Job -> V1ObjectMeta
            -> V1JobStatus
            -> V1JobSpec -> V1PodTemplate -> V1PodTemplateSpec -> V1Container
        """

        """
        vorher: name,
                container_image,
                namespace="default",
                container_name="jobcontainer",
                env_vars={}
        """

        # Create the job definition
        # _, image_name = job.image.split("/")
        # image_name = image_name.replace("_", "-")
        # name = f"{image_name}-{self.id_generator()}"

        body = client.V1Job(api_version="batch/v1", kind="Job")
        # Each JOB must have a different name!
        body.metadata = client.V1ObjectMeta(
            namespace=job.namespace, name=job.cluster_name)
        body.status = client.V1JobStatus()

        template = client.V1PodTemplate()
        template.template = client.V1PodTemplateSpec()

        # Passing Arguments in Env:
        env_list = []
        for env_name, env_value in job.env_vars.items():
            env_list.append(client.V1EnvVar(name=env_name, value=env_value))
        env_list.append(client.V1EnvVar(name="config_path",
                                        value=self.container_config_path)
                        )

        image = job.image + ":" + job.version
        container = client.V1Container(
            name=job.cluster_name, image=image, env=env_list)

        template.template.spec = client.V1PodSpec(containers=[container],
                                                  restart_policy="Never")

        template._template._spec.volumes = self.create_volume_from_configmap(
            job.config_maps)

        template._template._spec._containers[0].volume_mounts = self.create_volume_mount(
            job.config_maps)

        # And finally we can create our V1JobSpec
        body.spec = client.V1JobSpec(ttl_seconds_after_finished=600,
                                     template=template.template)

        return body

    def kube_create_job(self, job):
        body = self.kube_create_job_object(job)
        try:
            api_response = self.batch_api.create_namespaced_job(
                "default", body, pretty=True)
            # print(api_response)
        except ApiException as e:
            print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)
        return api_response

    def kube_create_deployment_object(self, deployment):
        # Passing Arguments in Env:
        env_list = []
        for env_name, env_value in deployment.env_vars.items():
            env_list.append(client.V1EnvVar(
                name=env_name, value=env_value))
        env_list.append(client.V1EnvVar(name="config_path",
                                        value=self.container_config_path)
                        )

        # Configureate Pod template container
        container = client.V1Container(
            name=deployment.cluster_name,
            image=deployment.image + ":" + deployment.version,
            env=env_list
            # ports=[client.V1ContainerPort(container_port=80)],
            # resources=client.V1ResourceRequirements(
            #     requests={"cpu": "100m", "memory": "200Mi"},
            #     limits={"cpu": "500m", "memory": "500Mi"},
            # ),
        )

        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={"app": deployment.cluster_name}),
            spec=client.V1PodSpec(containers=[container]),
        )
        template._spec.volumes = self.create_volume_from_configmap(
            deployment.config_maps)

        template._spec._containers[0].volume_mounts = self.create_volume_mount(
            deployment.config_maps)

        # Create the specification of deployment
        spec = client.V1DeploymentSpec(
            replicas=1, template=template, selector={
                "matchLabels":
                {"app": deployment.cluster_name}})

        # Instantiate the deployment object
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment.cluster_name),
            spec=spec,
        )

        return deployment

    def kube_create_deployment(self, deployment):
        # Create deployement
        resp = self.apps_api.create_namespaced_deployment(
            body=deployment, namespace="default"
        )

        print(f"\n[INFO] deployment {deployment.metadata.name} created.\n")
        # print("%s\t%s\t\t\t%s\t%s" %
        #       ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
        # print(
        #     "%s\t\t%s\t%s\t\t%s\n"
        #     % (
        #         resp.metadata.namespace,
        #         resp.metadata.name,
        #         resp.metadata.generation,
        #         resp.spec.template.spec.containers[0].image,
        #     )
        # )

    def kube_delete_deployment(self, deployment):
        # Delete deployment
        resp = self.apps_api.delete_namespaced_deployment(
            name=deployment.cluster_name,
            namespace="default",
            body=client.V1DeleteOptions(
                propagation_policy="Foreground", grace_period_seconds=0),
        )
        print(f"\n[INFO] deployment {deployment.cluster_name} deleted.")

    def get_pod_metadata(self):
        ret = self.core_api.list_pod_for_all_namespaces(watch=False)
        pod_list = [(i.status.pod_ip, i.metadata.namespace,
                     i.metadata.name) for i in ret.items]

        return pod_list

    def get_jobs_from_pipelines(self, pipelines):

        job_list = []

        for pipeline in pipelines:
            for module_name, module_info in pipeline:
                name = module_name
                image = module_info["container"]["Image"]
                version = module_info["container"]["Version"]
                # parameter = module_info["parameter"]

                cm_list = []
                for cm in module_info["container"]["Config_Maps"]:
                    cm_list.append(ConfigMap(**cm))

                job_list.append(
                    Job(name=name, image=image, version=version, config_maps=cm_list))
        return job_list

    def kube_delete_empty_pods(self, namespace='default', phase='Succeeded'):
        """
        Pods are never empty, just completed the lifecycle.
        As such they can be deleted.
        Pods can be without any running container in 2 states:
        Succeeded and Failed. This call doesn't terminate Failed pods by default.
        """
        # List the pods
        try:
            pods = self.core_api.list_namespaced_pod(namespace,
                                                     pretty=True,
                                                     timeout_seconds=60)
        except ApiException as e:
            print("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

        for pod in pods.items:
            podname = pod.metadata.name
            try:
                if pod.status.phase == phase:
                    api_response = self.core_api.delete_namespaced_pod(
                        podname, namespace)
                    print(f"Deleted pod {podname}")
                # else:
                #     print("Pod: {} still not done... Phase: {}".format(
                #         podname, pod.status.phase))
            except ApiException as e:
                print(
                    "Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)

        return

    def kube_cleanup_finished_jobs(self, namespace='default', state='Finished'):
        """
        Since the TTL flag (ttl_seconds_after_finished) is still in alpha (Kubernetes 1.12) jobs need to be cleanup manually
        As such this method checks for existing Finished Jobs and deletes them.
        By default it only cleans Finished jobs. Failed jobs require manual intervention or a second call to this function.
        Docs: https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/#clean-up-finished-jobs-automatically
        For deletion you need a new object type! V1DeleteOptions! But you can have it empty!
        CAUTION: Pods are not deleted at the moment. They are set to not running, but will count for your autoscaling limit, so if
                pods are not deleted, the cluster can hit the autoscaling limit even with free, idling pods.
                To delete pods, at this moment the best choice is to use the kubectl tool
                ex: kubectl delete jobs/JOBNAME.
                But! If you already deleted the job via this API call, you now need to delete the Pod using Kubectl:
                ex: kubectl delete pods/PODNAME
        """
        try:
            jobs = self.batch_api.list_namespaced_job(namespace,
                                                      # include_uninitialized=False,
                                                      pretty=True,
                                                      timeout_seconds=60)
            # print(jobs)
        except ApiException as e:
            print("Exception when calling BatchV1Api->list_namespaced_job: %s\n" % e)

        # Now we have all the jobs, lets clean up
        # We are also logging the jobs we didn't clean up because they either failed or are still running
        for job in jobs.items:
            jobname = job.metadata.name
            jobstatus = job.status.conditions
            if job.status.succeeded == 1:
                # Clean up Job
                try:
                    # What is at work here. Setting Grace Period to 0 means delete ASAP. Otherwise it defaults to
                    # some value I can't find anywhere. Propagation policy makes the Garbage cleaning Async
                    api_response = self.batch_api.delete_namespaced_job(jobname,
                                                                        namespace,
                                                                        grace_period_seconds=0,
                                                                        propagation_policy='Background')
                    print(f"Deleted job: {jobname}")
                except ApiException as e:
                    print(
                        "Exception when calling BatchV1Api->delete_namespaced_job: %s\n" % e)
            # else:
            #     if jobstatus is None and job.status.active == 1:
            #         jobstatus = 'active'
            #     print("Job: {} not cleaned up. Current status: {}".format(
            #         jobname, jobstatus))

        # Now that we have the jobs cleaned, let's clean the pods
        self.kube_delete_empty_pods(namespace)
        # And we are done!
        return
