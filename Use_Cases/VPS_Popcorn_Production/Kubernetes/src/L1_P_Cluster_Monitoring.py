import os
from time import sleep

from Big_Data_Platform.Kubernetes.Cognition.example.src.classes.KubeAPI import KubeAPI
from Big_Data_Platform.Kubernetes.Kafka_Client.Confluent_Kafka_Python.src.classes.CKafkaPC import KafkaPC


def send_job_metrics():
    print("Entering function send_job_metrics()")
    job_res = k_api.get_job_metrics()

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

        new_data_point = {
            "algorithm": job,
            "CPU_ms": cpu.m,
            "RAM": mem.m,
        }
        print(f"Send: {new_data_point}")
        new_pc.send_msg(new_data_point)


k_api = KubeAPI()
k_api.init_kube_connection()

env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}

new_pc = KafkaPC(**env_vars)

while True:
    send_job_metrics()
    k_api.kube_cleanup_finished_jobs()
    sleep(1)
