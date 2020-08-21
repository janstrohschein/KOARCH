import json
from .knowledge import knowledgebase
from fastapi.testclient import TestClient

client = TestClient(knowledgebase)


def test_feasible_pipelines():

    knowledge_json = json.loads('[[["1st_feature_pp_function", {"parameter": "parameters", "input": "raw_data"}],\
        ["Kriging", {"parameter": "parameters", "metadata": "", "input": "preprocessed features"}]],\
        [["some_data_pp_function", {"parameter": "parameters", "input": "raw_data"}], ["2nd_feature_pp_function",\
        {"parameter": "parameters", "input": "preprocessed data"}], ["Kriging", {"parameter": "parameters",\
        "metadata": "", "input": "preprocessed features"}]], [["CMAES", {"parameter": "parameters",\
        "input": "raw_data"}]]]')

    response = client.get("/knowledge/feasible_pipelines/?use_case=Optimization&goal=minimize&feature=minimum")
    response_pipelines = json.loads(response.text)
    assert response_pipelines == knowledge_json
    assert response.status_code == 200
