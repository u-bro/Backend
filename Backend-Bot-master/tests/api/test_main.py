import pytest

from tests.conftest import GLOBAL_CLIENT as client, GLOBAL_TELEGRAM_DATA


# @pytest.mark.asyncio
# async def test_hello_world_unauthenticated():
#     response = client.get("/")
#     assert response.status_code == 401


@pytest.mark.asyncio
async def test_hello_world_authenticated():
    response = client.get("/", headers={"Authorization": f"{GLOBAL_TELEGRAM_DATA}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
