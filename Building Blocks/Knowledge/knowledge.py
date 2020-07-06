import yaml
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse


def import_knowledge(knowledge_path="knowledge.yaml"):

    with open(knowledge_path, "r") as ymlfile:
        knowledge = yaml.load(ymlfile, Loader=yaml.FullLoader)

    return knowledge


knowledgebase = FastAPI()

knowledge = import_knowledge()


@knowledgebase.get("/knowledge/")
async def get_knowledge():
    """ Returns the complete knowledgebase. """
    response = JSONResponse(knowledge, status_code=200)
    return response


@knowledgebase.get("/knowledge/{usecase}/")
async def get_usecase(usecase: str):
    """ Filters the knowledge for a specific usecase. """

    usecase_knowledge = knowledge.get(usecase, "Key does not exist")
    status_code = 400 if usecase_knowledge == "Key does not exist" else 200

    return JSONResponse(usecase_knowledge, status_code=status_code)


@knowledgebase.put("/import_knowledge/")
async def import_knowledge(file: UploadFile = File(...)):
    """ Imports a YAML file as new knowledgebase. """

    content = await file.read()
    await file.close()
    content_yaml = yaml.load(content, Loader=yaml.FullLoader)
    for key, value in content_yaml.items():
        knowledge[key] = value

    return JSONResponse(content={"knowledge": "updated"}, status_code=200)


@knowledgebase.get("/export_knowledge/")
async def export_knowledge():
    """ Exports the current content of the knowledgebase into a YAML file."""

    with open("knowledge_temp.yaml", "w") as ymlfile:
        yaml.dump(knowledge, ymlfile)

    return FileResponse(path="knowledge_temp.yaml", filename='knowledge.yaml')
