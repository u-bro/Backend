from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.backend.deps.get_current_user import get_current_user
from app.backend.routers.car_photo import CarPhotoRouter
from app.schemas.car_photo import CarPhotoSchema


SIGNED_PHOTO = "https://s3.selcdn.ru/test-bucket/front?X-Amz-Signature=test"
LIST_PATH = "/api/v1/car-photos/car/2"
IMAGE_PATH = LIST_PATH + "/photos/7/image"


@pytest.fixture
def gallery():
    async def photos_for_car(session, car_id):
        if car_id != 2:
            return []
        return [CarPhotoSchema(id=7, car_id=2, type="FRONT", photo_url=SIGNED_PHOTO)]

    app = FastAPI()
    crud = SimpleNamespace(get_by_car_id=photos_for_car)
    app.include_router(CarPhotoRouter(crud, "/car-photos").router, prefix="/api/v1")

    @app.middleware("http")
    async def attach_session(request, call_next):
        confirmed = SimpleNamespace(status="confirmed")
        result = Mock()
        result.scalar_one_or_none.return_value = confirmed
        request.state.session = SimpleNamespace(execute=AsyncMock(return_value=result))
        return await call_next(request)

    with TestClient(app, follow_redirects=False) as client:
        yield app, client


def test_android_image_redirect_uses_same_api_origin_and_checks_access(gallery):
    app, client = gallery
    assert client.get(IMAGE_PATH).status_code == 401
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(phone="test", role=SimpleNamespace(code="user"))
    listing = client.get(LIST_PATH, headers={"User-Agent": "okhttp/4.12.0", "X-Forwarded-Proto": "https"})
    assert listing.status_code == 200
    assert listing.json()[0]["photo_url"] == f"https://testserver{IMAGE_PATH}"
    redirect = client.get(IMAGE_PATH)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == SIGNED_PHOTO
    assert "no-store" in redirect.headers["cache-control"]
    assert client.get(IMAGE_PATH.replace("/car/2", "/car/3")).status_code == 404
    assert client.get(IMAGE_PATH.replace("/photos/7", "/photos/8")).status_code == 404


def test_other_image_loaders_receive_the_original_signed_url(gallery):
    app, client = gallery
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(phone="test", role=SimpleNamespace(code="user"))
    assert client.get(LIST_PATH, headers={"User-Agent": "CFNetwork"}).json()[0]["photo_url"] == SIGNED_PHOTO
