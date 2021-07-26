from typing import Optional
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

CPPS_Controller = FastAPI(root_path="/cognition")


class Parameters(BaseModel):
    algorithm: Optional[str] = None
    x: Optional[float] = -1


production_parameters = Parameters(x=0, algorithm="init")


@CPPS_Controller.get("/production_parameters/", response_model=Parameters)
async def get_items():
    return production_parameters


@CPPS_Controller.put("/production_parameters/", response_model=Parameters)
async def update_items(parameters: Parameters):
    production_parameters.x = parameters.x
    production_parameters.algorithm = parameters.algorithm
    return production_parameters


@CPPS_Controller.get("/production_parameter/{parameter}", response_model=Parameters)
async def get_item(parameter: str):
    result = ""
    status_code = 400

    if parameter == 'x':
        status_code = 200
        result = production_parameters.x
    elif parameter == 'algorithm':
        status_code = 200
        result = production_parameters.algorithm
    else:
        result = 'Key does not exist'

    # parameter = production_parameters.fields.get(parameter, "Key does not exist")
    # status_code = 400 if parameter == "Key does not exist" else 200

    return JSONResponse(result, status_code=status_code)


@CPPS_Controller.patch("/production_parameter/{parameter}", response_model=Parameters)
async def update_item(parameter: str, value):

    if parameter == 'x':
        production_parameters.x = value
    elif parameter == 'algorithm':
        production_parameters.algorithm = value

    return production_parameters
