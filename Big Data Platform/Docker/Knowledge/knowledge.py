import yaml
# import json
import pydash
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse


def import_knowledge(knowledge_path="knowledge.yaml"):

    with open(knowledge_path, "r") as ymlfile:
        knowledge = yaml.load(ymlfile, Loader=yaml.FullLoader)

    return knowledge


def get_from_knowledge(knowledge, search_base, search):

    result = None
    search_string = search_base + '.' + search

    try:
        result = pydash.get(knowledge, search_string)
    except Exception as e:
        print(f'Error while searching: {search_string}, Error: {e}')

    return result


def get_pipelines(knowledge, search_base, search, parent=None, pipelines=[]):

    result = get_from_knowledge(knowledge, search_base, search)

    if result is None:
        return pipelines

    for key, values in result.items():
        pipeline = (key, values)

        if parent is not None:
            pipeline = (pipeline, *parent)
        else:
            pipeline = (pipeline,)

        if values['input'] == 'raw_data':
            pipelines.append(pipeline)
        else:

            pipelines = get_pipelines(knowledge, search_base, values['input'], pipeline, pipelines)

    return pipelines


knowledgebase = FastAPI()
knowledge = import_knowledge()

# local path for testing
# knowledge = import_knowledge("Big Data Platform/Docker/Knowledge/data/knowledge.yaml")


@knowledgebase.get("/knowledge/")
async def get_knowledge():
    """ Returns the complete knowledgebase. """
    response = JSONResponse(knowledge, status_code=200)
    return response


@knowledgebase.get("/knowledge/usecase/")
async def get_usecase(usecase: str):
    """ Filters the knowledge for a specific usecase.\n
    Example Usecase: Optimization
    """

    usecase_knowledge = knowledge.get(usecase, "Key does not exist")
    status_code = 400 if usecase_knowledge == "Key does not exist" else 200

    return JSONResponse(usecase_knowledge, status_code=status_code)


@knowledgebase.get("/knowledge/feasible_pipelines/")
async def get_feasible_pipelines(use_case=None, goal=None, feature=None):
    """ Filters the knowledgebase and returns feasible pipelines.\n
    Example Input:\n
    use_case = Optimization\n
    goal = minimize\n
    feature = minimum\n
    """

    if use_case is None or goal is None or feature is None:
        return JSONResponse("Need use_case, goal and feature", status_code=400)

    search_base = f"{use_case}.{goal}.{feature}"

    pipeline_start = 'algorithms'  # brauchen wir einen dynamischen Start? wie können wir diesen kennzeichnen?

    pipelines = get_pipelines(knowledge, search_base, pipeline_start, pipelines=[])
    return JSONResponse(pipelines, status_code=200)


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
