import pytest

from tests.conftest import GLOBAL_CLIENT as client, GLOBAL_TELEGRAM_DATA


# @pytest.mark.asyncio
# async def test_batch_create():
#     gpu_data = [
#         {
#             "id": 2,
#             "name": "GPU 1",
#             "income": 100.0,
#             "price": 200,
#             "rarity": 1,
#             "algorithm_type": "SHA256",
#             "coin_type": "BTC",
#             "is_crafted": False
#         },
#         {
#             "id": 3,
#             "name": "GPU 2",
#             "income": 150.0,
#             "price": 250,
#             "rarity": 2,
#             "algorithm_type": "SHA256",
#             "coin_type": "ETH",
#             "is_crafted": True
#         }
#     ]
#
#     response = client.post("/gpu/batch", json=gpu_data, headers={"Authorization": f"{GLOBAL_TELEGRAM_DATA}"})
#     assert response.status_code == 201
#     assert len(response.json()) == 2


# @pytest.mark.asyncio
# async def test_get_paginated():
#     response = client.get("/gpu?page=1&page_size=2", headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#
#
# @pytest.mark.asyncio
# async def test_get_count():
#     response = client.get("/gpu/count", headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 200
#     assert isinstance(response.json(), int)
#
#
# @pytest.mark.asyncio
# async def test_get_by_id():
#     response = client.get("/gpu/1", headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 200
#     assert isinstance(response.json(), dict)
#
#
# @pytest.mark.asyncio
# async def test_create():
#     gpu_data = {
#         "id": 1,
#         "name": "Test GPU",
#         "income": 100.0,
#         "price": 200,
#         "rarity": 1,
#         "algorithm_type": "SHA256",
#         "coin_type": "BTC",
#         "is_crafted": False
#     }
#     response = client.post("/gpu", json=gpu_data, headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 201
#     assert response.json()["name"] == gpu_data["name"]
#
#
# @pytest.mark.asyncio
# async def test_update():
#     gpu_data = {
#         "id": 1,
#         "name": "Updated GPU",
#         "income": 150.0,
#         "price": 250,
#         "rarity": 2,
#         "algorithm_type": "SHA256",
#         "coin_type": "BTC",
#         "is_crafted": True
#     }
#
#     response = client.put("/gpu/1", json=gpu_data, headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 200
#     assert response.json()["name"] == gpu_data["name"]
#
#
# @pytest.mark.asyncio
# async def test_delete():
#     response = client.delete("/gpu/1", headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 204
#
#
