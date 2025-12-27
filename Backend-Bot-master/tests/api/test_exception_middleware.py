import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from app.backend.middlewares.exception import setup_error_middleware

app = FastAPI()
setup_error_middleware(app)

@app.get("/raise-http-exc")
def raise_http_exc():
    raise HTTPException(status_code=418, detail="I'm a teapot")

class Item(BaseModel):
    name: str

@app.post("/raise-validation")
def raise_validation(item: Item):
    return item

@app.get("/raise-exc")
def raise_exc():
    raise RuntimeError("fail")

client = TestClient(app)

def test_http_exception():
    resp = client.get("/raise-http-exc")
    assert resp.status_code == 418
    assert resp.json()["detail"] == "I'm a teapot"

def test_validation_error():
    resp = client.post("/raise-validation", json={"wrong_field": 123})
    assert resp.status_code == 400
    assert "detail" in resp.json()

def test_unexpected_exception():
    resp = client.get("/raise-exc")
    assert resp.status_code == 500
    assert resp.json()["detail"] == "Internal server error occurred. Please try again later."
