from app.crud.base import CrudBase
from app.models import DriverModerationInfo, DriverProfileModeration
from app.schemas.driver_moderation_info import DriverModerationInfoSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import delete, and_
from app.enum import DRIVER_DOCUMENT_TO_MODERATION_INFO_CODE


class DriverModerationInfoCrud(CrudBase[DriverModerationInfo, DriverModerationInfoSchema]):
    def __init__(self) -> None:
        super().__init__(DriverModerationInfo, DriverModerationInfoSchema)

    async def delete_by_driver_profile_id_and_doc_type(self, session: AsyncSession, driver_profile_id: int, doc_type: str):
        moderation_code = DRIVER_DOCUMENT_TO_MODERATION_INFO_CODE.get(doc_type)
        if not moderation_code:
            return

        moderation_info_id_subquery = (
            select(self.model.id)
            .where(self.model.code == moderation_code)
            .scalar_subquery()
        )

        await session.execute(
            delete(DriverProfileModeration).where(
                and_(
                    DriverProfileModeration.driver_profile_id == driver_profile_id,
                    DriverProfileModeration.driver_moderation_info_id == moderation_info_id_subquery,
                )
            )
        )

driver_moderation_info_crud = DriverModerationInfoCrud()
