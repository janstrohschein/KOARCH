from classes.KubeAPI import KubeAPI

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
print(f"Kafka uses CPU: {kafka_cpu} ({kafka_cpu_per}%), Memory: {kafka_mem} ({kafka_mem_per}%)")
