from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

CPPS_Controller = FastAPI()

production_parameters = {
    "x": 4000.0,
}


@CPPS_Controller.get("/production_parameters/")
async def read_items():
    return JSONResponse(production_parameters, status_code=200)


@CPPS_Controller.get("/production_parameter/{parameter}")
async def read_item(parameter: str):

    parameter = production_parameters.get(parameter, "Key does not exist")
    status_code = 400 if parameter == "Key does not exist" else 200

    return JSONResponse(parameter, status_code=status_code)


@CPPS_Controller.put("/production_parameter/{parameter}")
async def update_item(parameter: str, value: float):
    update_item_encoded = jsonable_encoder(value)
    production_parameters[parameter] = update_item_encoded
    return JSONResponse(update_item_encoded, status_code=200)
