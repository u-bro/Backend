from app.crud.base import CrudBase
from app.models.driver_document import DriverDocument
from app.schemas.driver_document import DriverDocumentSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class DriverDocumentCrud(CrudBase[DriverDocument, DriverDocumentSchema]):
    def __init__(self) -> None:
        super().__init__(DriverDocument, DriverDocumentSchema)

    async def get_by_driver_profile_id(self, session: AsyncSession, driver_profile_id: int, **kwargs) -> list[DriverDocumentSchema]:
        existing = await session.execute(select(self.model).where(self.model.driver_profile_id == driver_profile_id))
        items = existing.scalars().all()
        return [self.schema.model_validate(item) for item in items]

driver_document_crud = DriverDocumentCrud()
