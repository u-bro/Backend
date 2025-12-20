import pytest
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

@pytest.mark.asyncio
def test_get_ride_receipt():
    ride_id = 123
    response = client.get(f"/api/v1/documents/ride/{ride_id}/receipt")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline; filename=receipt_")
    assert response.content

@pytest.mark.asyncio
def test_get_ride_receipt_download():
    ride_id = 123
    response = client.get(f"/api/v1/documents/ride/{ride_id}/receipt?download=true")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("attachment; filename=receipt_")
    assert response.content
