from typing import Any, Dict, List, Optional
from app.crud.base import CrudBase
from app.models.gpu import Gpu
from app.schemas import GpuSchema
from sqlalchemy.ext.asyncio import AsyncSession


class CrudGpu(CrudBase[Gpu, GpuSchema]):
    async def get_paginated_with_filters(
        self, 
        session: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        filters: Dict[str, Any] = {},
    ):
        return await super().get_paginated_with_filters(session, page, page_size, filters, sort_by, sort_desc)


gpu_crud: CrudGpu = CrudGpu(Gpu, GpuSchema)
