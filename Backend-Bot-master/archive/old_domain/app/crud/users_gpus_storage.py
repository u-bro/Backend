from sqlalchemy import delete, update, select, and_, text
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.backend.utils.exceptions import DatabaseError, handle_pg_raised_exception
from app.backend.utils.httprespose import HTTP_RESPONSE_OK, bool_to_http_response
from app.crud.base import CrudBase
from app.models import UserGpuStorage, Gpu
from app.schemas import UserGpuStorageSchema, UserGpuStorageSchemaUpdate


class CrudUserGpuStorage(CrudBase):

    async def sell_gpu_half_price(self, session: AsyncSession, user_gpu_storage_id: int) -> bool:
        stmt = text("SELECT sell_gpu_half_price(:user_gpu_storage_id)").params(user_gpu_storage_id=user_gpu_storage_id)
        try: 
            result = await self.execute_get_one(session, stmt)
        except SQLAlchemyError as e:
            handle_pg_raised_exception(e)
                
        return bool_to_http_response(result)

    async def get_paginated_storage(self, session: AsyncSession, user_id: int, page: int = 1, page_size: int = 2, is_working: bool = None):
        offset = (page - 1) * page_size

        stmt = (
            select(UserGpuStorage, Gpu)
            .join(Gpu, UserGpuStorage.gpu_id == Gpu.id)
            .options(joinedload(UserGpuStorage.gpu))
            .where(UserGpuStorage.user_id == user_id)
        )

        if is_working is not None:
            stmt = stmt.where(UserGpuStorage.is_working == is_working)

        stmt = stmt.offset(offset).limit(page_size)

        result = await session.execute(stmt)
        return result.scalars().all()

    async def delete_from_storage(self, session: AsyncSession, id: int) -> UserGpuStorageSchema | None:
        stmt = (
            delete(self.model).
            where(UserGpuStorage.id == id)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def mount_gpu(self, session: AsyncSession, user_gpu_storage_id: int, user_gpu_storage: UserGpuStorageSchemaUpdate):
        stmt = (
            update(UserGpuStorage)
            .where(UserGpuStorage.id == user_gpu_storage_id)
            .values(is_working=user_gpu_storage.is_working)
            .returning(UserGpuStorage)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None

    async def purchase_gpu(self, session: AsyncSession, user_id: int, gpu_id: int) -> bool:
        stmt = text("SELECT purchase_gpu(:user_id, :gpu_id)").params(user_id=user_id, gpu_id=gpu_id)
        
        try: 
            result = await self.execute_get_one(session, stmt)
        except SQLAlchemyError as e:
            handle_pg_raised_exception(e)
            
        return bool_to_http_response(result)

    async def craft_gpu(self, session: AsyncSession, gpu_ids: list[int], user_id: int) -> str:
        stmt = (
            text("SELECT craft_gpu(:gpu_id1, :gpu_id2, :gpu_id3, :gpu_id4, :gpu_id5, :user_id)")
            .params(gpu_id1=gpu_ids[0], gpu_id2=gpu_ids[1], gpu_id3=gpu_ids[2], gpu_id4=gpu_ids[3], gpu_id5=gpu_ids[4], user_id=user_id)
        )
        result = await self.execute_get_one(session, stmt)
        return result


user_gpu_storage_crud: CrudUserGpuStorage = CrudUserGpuStorage(UserGpuStorage, UserGpuStorageSchema)
