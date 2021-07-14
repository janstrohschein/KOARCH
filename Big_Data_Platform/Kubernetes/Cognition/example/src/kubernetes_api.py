import hashlib
from pprint import pprint
import string
import random
import logging
import yaml
import sys
import os
import time
import requests
import json
from collections import defaultdict
from kubernetes import client, config, utils
import kubernetes.client
from kubernetes.client.rest import ApiException

# Set logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Setup K8 configs
config.load_kube_config("/mnt/c/Users/stroh/.kube/config")
v1 = client.CoreV1Api()

configuration = kubernetes.client.Configuration()
api_instance = kubernetes.client.BatchV1Api(
    kubernetes.client.ApiClient(configuration))


def list_pods():
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        print("%s\t%s\t%s" %
              (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


def kube_delete_empty_pods(namespace='default', phase='Succeeded'):
    """
    Pods are never empty, just completed the lifecycle.
    As such they can be deleted.
    Pods can be without any running container in 2 states:
    Succeeded and Failed. This call doesn't terminate Failed pods by default.
    """
    # The always needed object
    deleteoptions = client.V1DeleteOptions()
    # We need the api entry point for pods
    api_pods = client.CoreV1Api()
    # List the pods
    try:
        pods = api_pods.list_namespaced_pod(namespace,
                                            # include_uninitialized=False,
                                            pretty=True,
                                            timeout_seconds=60)
    except ApiException as e:
        logging.error(
            "Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

    for pod in pods.items:
        logging.debug(pod)
        podname = pod.metadata.name
        try:
            if pod.status.phase == phase:
                api_response = api_pods.delete_namespaced_pod(
                    podname, namespace)
                logging.info("Pod: {} deleted!".format(podname))
                logging.debug(api_response)
            else:
                logging.info("Pod: {} still not done... Phase: {}".format(
                    podname, pod.status.phase))
        except ApiException as e:
            logging.error(
                "Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)

    return


def kube_cleanup_finished_jobs(namespace='default', state='Finished'):
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
    deleteoptions = client.V1DeleteOptions()
    try:
        jobs = api_instance.list_namespaced_job(namespace,
                                                # include_uninitialized=False,
                                                pretty=True,
                                                timeout_seconds=60)
        # print(jobs)
    except ApiException as e:
        print("Exception when calling BatchV1Api->list_namespaced_job: %s\n" % e)

    # Now we have all the jobs, lets clean up
    # We are also logging the jobs we didn't clean up because they either failed or are still running
    for job in jobs.items:
        logging.debug(job)
        jobname = job.metadata.name
        jobstatus = job.status.conditions
        if job.status.succeeded == 1:
            # Clean up Job
            logging.info("Cleaning up Job: {}. Finished at: {}".format(
                jobname, job.status.completion_time))
            try:
                # What is at work here. Setting Grace Period to 0 means delete ASAP. Otherwise it defaults to
                # some value I can't find anywhere. Propagation policy makes the Garbage cleaning Async
                api_response = api_instance.delete_namespaced_job(jobname,
                                                                  namespace,
                                                                  grace_period_seconds=0,
                                                                  propagation_policy='Background')
                logging.debug(api_response)
            except ApiException as e:
                print(
                    "Exception when calling BatchV1Api->delete_namespaced_job: %s\n" % e)
        else:
            if jobstatus is None and job.status.active == 1:
                jobstatus = 'active'
            logging.info("Job: {} not cleaned up. Current status: {}".format(
                jobname, jobstatus))

    # Now that we have the jobs cleaned, let's clean the pods
    kube_delete_empty_pods(namespace)
    # And we are done!
    return


def kube_create_job_object(name, container_image, namespace="default", container_name="jobcontainer", env_vars={}):
    """
    Create a k8 Job Object
    Minimum definition of a job object:
    {'api_version': None, - Str
    'kind': None,     - Str
    'metadata': None, - Metada Object
    'spec': None,     -V1JobSpec
    'status': None}   - V1Job Status
    Docs: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Job.md
    Docs2: https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/#writing-a-job-spec
    Also docs are pretty pretty bad. Best way is to ´pip install kubernetes´ and go via the autogenerated code
    And figure out the chain of objects that you need to hold a final valid object So for a job object you need:
    V1Job -> V1ObjectMeta
          -> V1JobStatus
          -> V1JobSpec -> V1PodTemplate -> V1PodTemplateSpec -> V1Container

    Now the tricky part, is that V1Job.spec needs a .template, but not a PodTemplateSpec, as such
    you need to build a PodTemplate, add a template field (template.template) and make sure
    template.template.spec is now the PodSpec.
    Then, the V1Job.spec needs to be a JobSpec which has a template the template.template field of the PodTemplate.
    Failure to do so will trigger an API error.
    Also Containers must be a list!
    Docs3: https://github.com/kubernetes-client/python/issues/589
    """
    # Body is the object Body
    body = client.V1Job(api_version="batch/v1", kind="Job")
    # Body needs Metadata
    # Attention: Each JOB must have a different name!
    body.metadata = client.V1ObjectMeta(namespace=namespace, name=name)
    # And a Status
    body.status = client.V1JobStatus()
    # Now we start with the Template...
    template = client.V1PodTemplate()
    template.template = client.V1PodTemplateSpec()
    # Passing Arguments in Env:
    env_list = []
    for env_name, env_value in env_vars.items():
        env_list.append(client.V1EnvVar(name=env_name, value=env_value))
    container = client.V1Container(
        name=container_name, image=container_image, env=env_list)
    template.template.spec = client.V1PodSpec(
        containers=[container], restart_policy='Never')
    # And finaly we can create our V1JobSpec!
    body.spec = client.V1JobSpec(
        ttl_seconds_after_finished=600, template=template.template)
    return body


def kube_test_credentials():
    """
    Testing function.
    If you get an error on this call don't proceed. Something is wrong on your connectivty to
    Google API.
    Check Credentials, permissions, keys, etc.
    Docs: https://cloud.google.com/docs/authentication/
    """
    try:
        api_response = api_instance.get_api_resources()
        # logging.info(api_response)
    except ApiException as e:
        print("Exception when calling API: %s\n" % e)


def kube_create_job(image, parameter=None):
    # Create the job definition
    if parameter is None:
        parameter = {}
    # container_image = "hello-world"
    # name = container_image + id_generator()
    # name = f"{image}-{id_generator()}"
    name = id_generator()
    # body = kube_create_job_object(name, container_image, env_vars={"VAR": "TESTING"})
    body = kube_create_job_object(name, image, env_vars=parameter)
    try:
        api_response = api_instance.create_namespaced_job(
            "default", body, pretty=True)
        # print(api_response)
    except ApiException as e:
        print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)
    return


def id_generator(size=12, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def get_from_API(URL, parameters=None):
    result = ()

    try:
        api_request = requests.get(url=URL, params=parameters)
        result = json.loads(api_request.content)
    except Exception as e:
        print(f"Could not retrieve from API: {e}")

    return result


"""
To deploy a Kubernetes Job, we need to build the following objects:

Job object
    Contains a metadata object
    Contains a job spec object
        Contains a pod template object
            Contains a pod template spec object
                Contains a container object
"""

if __name__ == '__main__':

    # list_pods()

    # Testing Credentials
    # kube_test_credentials()
    # Cleanup dead jobs
    # kube_cleanup_finished_jobs()
    # kube_delete_empty_pods()
    # Create jobs

    """
    - check user input
    - check if algorithms are available, 
        if no algorithms available OR resources available instantiate more algorithms
    - get feasible pipeline OR testfunction winners
    - get parameter settings for each module in pipeline
    - create job for each module in pipeline
    - clean up finished jobs   
        - clean up finished pipelines instead? keep track of pipelines jobs?


    """

    """
    get info from config.yml?
    """

    # API_URL = "http://127.0.0.1:8001"
    # API_URL = new_pc.config['API_URL']
    API_URL = "http://api-knowledge-service.default:80"
    ENDPOINT_USER_INPUT = "/use_case/"
    URL_USER_INPUT = API_URL + ENDPOINT_USER_INPUT

    ENDPOINT_FEASIBLE_PIPELINES = "/knowledge/feasible_pipelines/"
    URL_FEASIBLE_PIPELINES = API_URL + ENDPOINT_FEASIBLE_PIPELINES

    """"""

    user_input = get_from_API(URL_USER_INPUT)
    feasible_pipelines = get_from_API(URL_FEASIBLE_PIPELINES, user_input)
    jobs = defaultdict(list)

    for pipeline in feasible_pipelines:
        # print(f"Pipeline: {pipeline}")
        for module_name, module_info in pipeline:
            image = module_info["metadata"]["Image"]
            parameter = module_info["parameter"]

            if parameter is None:
                if not jobs.get(image):
                    jobs[image].append({})
            else:
                jobs[image].append(parameter)

    # print(jobs)

    """
    - get parameter value, not allowed to be a dict
    """

    for job, parameters in jobs.items():
        for parameter in parameters:
            print(job, parameter)
            kube_create_job(job, parameter)

    # list_pods()

    sys.exit(0)
