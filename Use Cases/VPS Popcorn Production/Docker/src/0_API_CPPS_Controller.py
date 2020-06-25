from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder

CPPS_Controller = FastAPI()

production_parameters = {
    "x": 4000.0,
}


@CPPS_Controller.get("/production_parameters/")
async def read_items():
    return production_parameters


@CPPS_Controller.get("/production_parameter/{parameter}")
async def read_item(parameter: str):
    return production_parameters[parameter]


@CPPS_Controller.put("/production_parameter/{parameter}")
async def update_item(parameter: str, value: float):
    update_item_encoded = jsonable_encoder(value)
    production_parameters[parameter] = update_item_encoded
    return update_item_encoded
