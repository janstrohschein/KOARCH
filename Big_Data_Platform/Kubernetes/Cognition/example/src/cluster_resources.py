from classes.KubeAPI import KubeAPI
from pprint import pprint

k_api = KubeAPI()
k_api.init_kube_connection()

cluster_info = k_api.get_cluster_metrics()
print("Custom Cluster Summary:")
print(cluster_info)

cluster_cpu_avg = cluster_info.get_cpu_usage_perc_avg()
print(f"Average Cluster CPU usage: {cluster_cpu_avg}%")

pod_info = k_api.get_pod_metrics()
# print("Custom Pod Summary:")
# print(pod_info)

kafka_cpu = pod_info['kafka'].get_cpu_sum()
kafka_cpu_per = pod_info['kafka'].get_cpu_perc_sum()
kafka_mem = pod_info['kafka'].get_mem_sum()
kafka_mem_per = pod_info['kafka'].get_mem_perc_sum()
print(
    f"Kafka uses CPU: {kafka_cpu} ({kafka_cpu_per}%), Memory: {kafka_mem} ({kafka_mem_per}%)")


print("Job Summary:")
job_res = k_api.get_job_metrics()
pprint(job_res)

job_metrics = []

for job, job_info in job_res.items():
    cpu = 0
    mem = 0
    for container in job_info.containers:
        cpu += container.cpu_usage
        mem += container.mem_usage
    if cpu > 0:
        cpu = cpu.to('millicpu')
    if mem > 0:
        mem = mem.to('Mi')

    job_metrics.append((job, cpu.m, mem.m))

print("Job Metrics:")
print(job_metrics)
