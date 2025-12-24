from app.crud.base import CrudBase
from app.models.ride_status_history import RideStatusHistory
from app.schemas.ride_status_history import RideStatusHistorySchema


class RideStatusHistoryCrud(CrudBase[RideStatusHistory, RideStatusHistorySchema]):
    def __init__(self) -> None:
        super().__init__(RideStatusHistory, RideStatusHistorySchema)


ride_status_history_crud = RideStatusHistoryCrud()
