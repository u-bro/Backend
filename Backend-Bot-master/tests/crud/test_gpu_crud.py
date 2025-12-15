import copy
import pytest
from tests.conftest import async_session_maker
from app.crud import gpu_crud
from app.schemas import GpuSchemaCreate, GpuSchema


# @pytest.mark.asyncio
# async def test_get_paginated():
#     gpu_data_list = [{"name": f"GPU T1{i}", "income": 100.00 * i, "price": 500 * i, "rarity": i,
#                       "algorithm_type": "SHA-256", "coin_type": "BTC", "is_crafted": False} for i in range(1, 6)]
#     gpus = [GpuSchemaCreate(**data) for data in gpu_data_list]
#     async with async_session_maker() as db_session:
#         await gpu_crud.batch_create(db_session, gpus)

#         page_1 = await gpu_crud.get_paginated(db_session, page=1, page_size=2)
#         assert len(page_1) == 2 and isinstance(page_1[0], GpuSchema)

#         page_2 = await gpu_crud.get_paginated(db_session, page=2, page_size=2)
#         assert len(page_2) == 2 and isinstance(page_1[0], GpuSchema)


# @pytest.mark.asyncio
# async def test_create_gpu():
#     gpu_data = {
#         "name": "NVIDIA RTX 3090", "income": 500.50, "price": 1500,
#         "rarity": 5, "algorithm_type": "SHA-256", "coin_type": "BTC", "is_crafted": False
#     }
#     gpu = GpuSchemaCreate(**gpu_data)
#     async with async_session_maker() as db_session:
#         created_gpu = await gpu_crud.create(db_session, gpu)
#         assert created_gpu and created_gpu.name == "NVIDIA RTX 3090"
#         assert created_gpu.price == 1500


# @pytest.mark.asyncio
# async def test_get_by_id_gpu():
#     gpu_data = {
#         "name": "NVIDIA RTX 3080", "income": 400.00, "price": 1200,
#         "rarity": 4, "algorithm_type": "SHA-256", "coin_type": "BTC", "is_crafted": True
#     }
#     gpu = GpuSchemaCreate(**gpu_data)
#     async with async_session_maker() as db_session:
#         created_gpu = await gpu_crud.create(db_session, gpu)
#         gpu = await gpu_crud.get_by_id(db_session, created_gpu.id)
#         assert gpu and gpu.name == "NVIDIA RTX 3080" and gpu.is_crafted


# @pytest.mark.asyncio
# async def test_update_gpu():
#     gpu_data = {
#         "name": "NVIDIA RTX 3070", "income": 300.00, "price": 800,
#         "rarity": 3, "algorithm_type": "Ethash", "coin_type": "ETH", "is_crafted": False
#     }
#     gpu = GpuSchemaCreate(**gpu_data)
#     async with async_session_maker() as db_session:
#         created_gpu = await gpu_crud.create(db_session, gpu)
#         updated_gpu = await gpu_crud.update(db_session, created_gpu.id, GpuSchemaCreate(**{"price": 850, "rarity": 4}))
#         assert updated_gpu and updated_gpu.price == 850 and updated_gpu.rarity == 4


# @pytest.mark.asyncio
# async def test_delete_gpu():
#     gpu_data = {
#         "name": "AMD RX 6800", "income": 250.00, "price": 700,
#         "rarity": 3, "algorithm_type": "Ethash", "coin_type": "ETH", "is_crafted": False
#     }
#     gpu = GpuSchemaCreate(**gpu_data)
#     async with async_session_maker() as db_session:
#         created_gpu = await gpu_crud.create(db_session, gpu)
#         deleted_gpu = await gpu_crud.delete(db_session, created_gpu.id)
#         assert deleted_gpu and deleted_gpu.name == "AMD RX 6800"
#         assert await gpu_crud.get_by_id(db_session, created_gpu.id) is None


# @pytest.mark.asyncio
# async def test_batch_delete_and_create_gpu():
#     gpu_data_list = [
#         {"name": "NVIDIA RTX 2080", "income": 500.50, "price": 1500, "rarity": 5,
#          "algorithm_type": "SHA-256", "coin_type": "BTC", "is_crafted": False},
#         {"name": "AMD RX 6600", "income": 250.00, "price": 700, "rarity": 3,
#          "algorithm_type": "Ethash", "coin_type": "ETH", "is_crafted": False}
#     ]
#     gpus = [GpuSchemaCreate(**data) for data in gpu_data_list]
#     async with async_session_maker() as db_session:
#         created_gpus = await gpu_crud.batch_create(db_session, gpus)
#         created_ids = [gpu.id for gpu in created_gpus]
#         deleted_gpus = await gpu_crud.batch_delete(db_session, created_ids)
#         assert len(deleted_gpus) == 2 and all(gpu.id in created_ids for gpu in deleted_gpus)

#         for gpu_id in created_ids:
#             assert await gpu_crud.get_by_id(db_session, gpu_id) is None


# @pytest.mark.asyncio
# async def test_get_count():
#     async with async_session_maker() as db_session:
#         count = await gpu_crud.get_count(db_session)
#         assert count == 10


@pytest.mark.asyncio
async def test_test(client, fill_db):
    inserted_data = fill_db
    inserted_data = copy.deepcopy(inserted_data)
    
