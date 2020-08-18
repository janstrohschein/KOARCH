from ..L0_API_CPPS_Controller import CPPS_Controller
from fastapi.testclient import TestClient

client = TestClient(CPPS_Controller)


def test_read_items():
    response = client.get("/production_parameters/")
    assert response.json() == {"x": 4000.0}


def test_read_item():
    response = client.get("/production_parameter/x")
    assert response.status_code == 200
    assert response.json() == 4000.0

    response = client.get("/production_parameter/xyz")
    assert response.status_code == 400
    assert response.json() == "Key does not exist"


def test_update_item():
    response = client.put("/production_parameter/x?value=5000.0")
    assert response.status_code == 200
    assert response.json() == 5000.0

    response = client.get("/production_parameter/x")
    assert response.json() == 5000.0
