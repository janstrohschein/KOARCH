from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

CPPS_Controller = FastAPI()

class Parameters(BaseModel):
    algorithm: str
    x: float

production_parameters = Parameters(x=4000.0, algorithm="init")


@CPPS_Controller.get("/production_parameters/", response_model=Parameters)
async def get_items():
    return production_parameters

@CPPS_Controller.put("/production_parameters/", response_model=Parameters)
async def update_items(parameters: Parameters):
    production_parameters.x = parameters.x
    production_parameters.algorithm = parameters.algorithm
    return production_parameters

@CPPS_Controller.get("/production_parameter/{parameter}")
async def get_item(parameter: str):

    parameter = production_parameters.get(parameter, "Key does not exist")
    status_code = 400 if parameter == "Key does not exist" else 200

    return JSONResponse(parameter, status_code=status_code)


@CPPS_Controller.put("/production_parameter/{parameter}")
async def update_item(parameter: str, value: float):
    update_item_encoded = jsonable_encoder(value)
    production_parameters[parameter] = update_item_encoded
    return JSONResponse(update_item_encoded, status_code=200)
