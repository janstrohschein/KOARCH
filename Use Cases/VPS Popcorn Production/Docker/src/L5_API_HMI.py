import os
import json
import sys
from enum import Enum
import yaml
from fastapi import FastAPI
from fastapi.responses import JSONResponse


def read_config(config_path, config_section):
    config = {}
    try:
        with open(config_path, "r") as ymlfile:
            config = yaml.load(ymlfile, Loader=yaml.FullLoader)
            for section in config_section:
                for key, value in config[section].items():
                    config[key] = value

    except Exception as e:
        print(f'Failed to read the config: {repr(e)}')
        sys.exit()
    return config


config_path = os.getenv('config_path')
config_section = os.getenv('config_section')

if config_path is not None and config_section is not None:
    config_section = config_section.replace(' ', '').split(',')
    config = read_config(config_path, config_section)


results = {key: [] for key in config["API_OUT"]}
custom_enum_values = {key: key for key in config["API_OUT"]}

TypeEnum = Enum("TypeEnum", custom_enum_values)

results_api = FastAPI()


@results_api.get("/topics")
async def get_results():

    return JSONResponse(results, status_code=200)


@results_api.get("/topic/{topic_name}")
async def get_result(topic_name: TypeEnum):

    return JSONResponse(results[topic_name.value], status_code=200)


@results_api.post("/topic/{topic_name}")
async def post_result(topic_name: TypeEnum, row: str):

    row_encoded = json.loads(row)
    results[topic_name.value].append(row_encoded)
    return JSONResponse(row_encoded, status_code=200)
