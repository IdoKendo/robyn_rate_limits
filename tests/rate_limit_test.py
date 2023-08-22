import platform
import sys

import pytest
import requests

base_url = f"http://127.0.0.1:8080/{platform.system()}/{sys.version_info.minor}"


@pytest.mark.usefixtures("_session")
def test_integration():
    response = requests.get(f"{base_url}/test")
    assert response.status_code == 200
    response = requests.get(f"{base_url}/test")
    assert response.status_code == 200
    response = requests.get(f"{base_url}/test")
    assert response.status_code == 200
    response = requests.get(f"{base_url}/test")
    assert response.status_code == 429
    response = requests.get(f"{base_url}/test")
    assert response.status_code == 429


@pytest.mark.usefixtures("_session")
def test_integration_per_route():
    response = requests.get(f"{base_url}/harsh_test")
    assert response.status_code == 200
    response = requests.get(f"{base_url}/harsh_test")
    assert response.status_code == 429
    response = requests.get(f"{base_url}/test")
    assert response.status_code == 200


@pytest.mark.usefixtures("_session")
def test_integration_with_redis():
    response = requests.get(f"{base_url}/harsh_test")
    assert response.status_code == 200
    response = requests.get(f"{base_url}/harsh_test")
    assert response.status_code == 429
    response = requests.get(f"{base_url}/test")
    assert response.status_code == 200
