import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.backend.openapi_schema import custom_openapi

app = FastAPI()

@app.get("/ping")
def ping():
    return {"pong": True}

# Устанавливаем кастомную openapi-функцию
app.openapi = lambda: custom_openapi(app)

client = TestClient(app)

def test_main_openapi_schema(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "components" in data
    assert "APIKeyHeader" in data["components"]["securitySchemes"]

def test_custom_openapi_schema():
    app.openapi_schema = None  # сброс кеша!
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "components" in data
    assert "securitySchemes" in data["components"]
    assert "APIKeyHeader" in data["components"]["securitySchemes"]
    assert data["components"]["securitySchemes"]["APIKeyHeader"]["type"] == "apiKey"
    assert data["components"]["securitySchemes"]["APIKeyHeader"]["in"] == "header"
    assert data["components"]["securitySchemes"]["APIKeyHeader"]["name"] == "Authorization"
    assert data["security"] == [{"APIKeyHeader": []}]

def test_custom_openapi_direct():
    app.openapi_schema = None
    schema1 = custom_openapi(app)
    schema2 = custom_openapi(app)
    assert schema1 is schema2
    assert "components" in schema1
    assert "APIKeyHeader" in schema1["components"]["securitySchemes"]
