from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import update

from app.logger import logger
from app.crud.base import CrudBase
from app.models import User
from app.schemas import BalanceUpdateResponse, UserSchema


class CrudUser(CrudBase):
    async def update_user_balance(self, session: AsyncSession, user_id: int) -> BalanceUpdateResponse | None:
        stmt = text("SELECT update_user_balance(:user_id)").params(user_id=user_id)
        
        try: 
            result = await self.execute_get_one(session, stmt)
        except SQLAlchemyError as e:
            logger.exception("DB error in update_user_balance")
            raise
        
        if result is None:
            return None
        # result is a Row or scalar - convert to dict for validation
        if hasattr(result, '_mapping'):
            return BalanceUpdateResponse.model_validate(dict(result._mapping))
        elif isinstance(result, dict):
            return BalanceUpdateResponse.model_validate(result)
        else:
            # If it's a single value from the function, wrap it
            return BalanceUpdateResponse(success=bool(result))


    async def delete(self, session: AsyncSession, id: int) -> UserSchema | None:
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(is_active=False)
            .returning(self.model)
        )
        result = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(result) if result else None


user_crud: CrudUser = CrudUser(User, UserSchema)