from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.utils.httprespose import HTTP_RESPONSE_FUCK, HTTP_RESPONSE_OK, bool_to_http_response
from app.crud.base import CrudBase
from app.models import Order
from app.schemas import OrderSchema, OrderSchemaCreate


class OrderGpu(CrudBase):
    async def purchase_gpu_by_order(self, session: AsyncSession, buyer_id: int, order_id: int) -> bool:
        stmt = text("SELECT sell_gpu(:buyer_id, :order_id)").params(buyer_id=buyer_id, order_id=order_id)
        result = await self.execute_get_one(session, stmt)
        return bool_to_http_response(result)

    pass


order_crud: OrderGpu = OrderGpu(Order, OrderSchema)
