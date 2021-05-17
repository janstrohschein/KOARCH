import requests
import json
import time
import os

# from classes.KafkaPC import KafkaPC
from classes.CKafkaPC import KafkaPC
from classes.caai_util import ObjectiveFunction


env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}

new_pc = KafkaPC(**env_vars)

new_objective = ObjectiveFunction()
new_objective.load_data(
    data_path=new_pc.config["data_path"],
    x_columns=new_pc.config["x_columns"],
    y_columns=new_pc.config["y_columns"],
)
new_objective.fit_model()

N_INITIAL_DESIGN = new_pc.config["N_INITIAL_DESIGN"]
MAX_PRODUCTION_CYCLES = new_pc.config["MAX_PRODUCTION_CYCLES"]
phase = "init"
current_data_point = 0

time.sleep(5)

while current_data_point < MAX_PRODUCTION_CYCLES:

    if current_data_point == N_INITIAL_DESIGN:
        phase = "observation"

    # API_URL = "http://127.0.0.1:8000"
    API_URL = new_pc.config["API_URL"]
    ENDPOINT = "/production_parameters/"
    URL = API_URL + ENDPOINT

    print(f"\nProduction cycle {current_data_point}")
    print("Load the current x from the CPPS Controller")
    api_request = requests.get(url=URL)
    req_json = json.loads(api_request.content)
    new_x = req_json["x"]
    new_y = new_objective.get_objective(new_x)

    new_data_point = {
        "id": current_data_point,
        "phase": phase,
        "algorithm": req_json["algorithm"],
        "x": new_x,
        "y": new_y,
    }

    new_pc.send_msg(new_data_point)
    print(f"The CPPS produced with x={round(new_x, 3)} -> y={round(new_y, 3)}")
    current_data_point += 1
    time.sleep(5)
