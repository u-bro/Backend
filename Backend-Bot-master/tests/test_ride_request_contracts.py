import pytest
from pydantic import ValidationError

from app.config import DRIVER_PENDING_REQUEST_LIMIT
from app.const import ACTIVE_RIDE_STATUSES, RIDE_REQUEST_REMOVAL_REASONS
from app.crud.ride import ALLOWED_TRANSITIONS, STATUSES
from app.schemas.ride_drivers_request import RideDriversRequestUpdate


def test_ride_request_contract_constants():
    assert DRIVER_PENDING_REQUEST_LIMIT == 10
    assert ACTIVE_RIDE_STATUSES == ("waiting_commission", "accepted", "on_the_way", "arrived", "started")
    assert set(RIDE_REQUEST_REMOVAL_REASONS) == {
        "selected_other_driver",
        "ride_canceled",
        "ride_expired",
        "driver_withdrawn",
        "driver_offline",
        "driver_assigned_elsewhere",
    }


def test_public_ride_request_update_only_accepts_selection():
    update = RideDriversRequestUpdate(status="accepted")
    assert update.status == "accepted"


def test_public_ride_request_update_rejects_removal_semantics():
    with pytest.raises(ValidationError):
        RideDriversRequestUpdate(status="canceled", removal_reason="driver_offline")


def test_ride_status_contract_and_ordinary_transitions():
    assert STATUSES == {
        "requested",
        "waiting_commission",
        "accepted",
        "on_the_way",
        "arrived",
        "started",
        "completed",
        "canceled",
    }
    assert ALLOWED_TRANSITIONS["accepted"] == {"on_the_way", "canceled"}
    assert ALLOWED_TRANSITIONS["on_the_way"] == {"arrived", "canceled"}
    assert ALLOWED_TRANSITIONS["arrived"] == {"started", "canceled"}
    assert ALLOWED_TRANSITIONS["started"] == {"completed"}
