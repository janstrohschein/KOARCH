import requests
import json
from pprint import pprint
from time import sleep

from Big_Data_Platform.Kubernetes.Cognition.example.src.classes.KubeAPI import KubeAPI, Deployment, ConfigMap


def get_from_API(URL, parameters=None):
    result = ()

    try:
        api_request = requests.get(url=URL, params=parameters)
        result = json.loads(api_request.content)
    except Exception as e:
        print(f"Could not retrieve from API: {e}")

    return result


k_api = KubeAPI()
k_api.init_kube_connection()

API_URL = "http://api-knowledge-service.default:80"
ENDPOINT_USER_INPUT = "/use_case/"
URL_USER_INPUT = API_URL + ENDPOINT_USER_INPUT

ENDPOINT_FEASIBLE_PIPELINES = "/knowledge/feasible_pipelines/"
URL_FEASIBLE_PIPELINES = API_URL + ENDPOINT_FEASIBLE_PIPELINES

user_input = get_from_API(URL_USER_INPUT)
feasible_pipelines = get_from_API(URL_FEASIBLE_PIPELINES, user_input)

algorithm = {"algorithm": "Kriging"}
api_info = {**user_input, **algorithm}


ENDPOINT_ALGORITHM = "/knowledge/algorithm/"
URL_ALGORITHM = API_URL + ENDPOINT_ALGORITHM
alg_info = get_from_API(URL_ALGORITHM, api_info)
print(alg_info)

name = "Kriging"
image = alg_info["container"]["Image"]
version = alg_info["container"]["Version"]

cm_list = []
for cm in alg_info["container"]["Config_Maps"]:
    cm_list.append(ConfigMap(**cm))

best_alg_dep = Deployment(name=name, image=image,
                          version=version, config_maps=cm_list)


# dep_obj = k_api.kube_create_deployment_object(best_alg_dep)
# k_api.kube_create_deployment(dep_obj)

# sleep(5)
k_api.kube_delete_deployment(best_alg_dep)

# while True:
#     if k_api.has_capacity():
#         job_list = k_api.get_jobs_from_pipelines(feasible_pipelines)
#         for job in job_list:
#             print(job)
#             k_api.kube_create_job(job)

#         pprint(k_api.get_pod_metadata())
#     else:
#         print("Waiting for resources..")
#     sleep(5)
