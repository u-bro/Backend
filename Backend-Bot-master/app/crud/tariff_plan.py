from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import insert, update

from app.crud.base import CrudBase
from app.models import TariffPlan
from app.schemas.tariff_plan import TariffPlanSchema

class CrudTariffPlan(CrudBase):
    async def update(self, session: AsyncSession, id: int, update_obj) -> TariffPlanSchema | None:
        now = datetime.utcnow()

        existing_result = await session.execute(select(self.model).where(self.model.id == id))
        existing: TariffPlan | None = existing_result.scalar_one_or_none()
        if existing is None:
            return None

        if getattr(existing, "effective_to", None) is not None:
            raise HTTPException(status_code=400, detail="Cannot update a closed tariff plan version")

        data = update_obj.model_dump(exclude_none=True)

        new_effective_from = data.get("effective_from") or now
        if getattr(existing, "effective_from", None) and new_effective_from <= existing.effective_from:
            raise HTTPException(status_code=400, detail="effective_from must be greater than previous effective_from")

        close_stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(effective_to=new_effective_from, updated_at=now)
            .returning(self.model)
        )
        closed = await self.execute_get_one(session, close_stmt)
        if closed is None:
            return None

        insert_data = {
            "name": data.get("name", existing.name),
            "base_fare": data.get("base_fare"),
            "rate_per_meter": data.get("rate_per_meter"),
            "multiplier": data.get("multiplier"),
            "rules": data.get("rules"),
            "effective_from": new_effective_from,
            "effective_to": data.get("effective_to"),
            "created_at": now,
            "updated_at": now,
        }

        stmt = insert(self.model).values(insert_data).returning(self.model)
        created = await self.execute_get_one(session, stmt)
        return self.schema.model_validate(created) if created else None

tariff_plan_crud = CrudTariffPlan(TariffPlan, TariffPlanSchema)
