import pytest
from pydantic import ValidationError

from app.config import DRIVER_PENDING_REQUEST_LIMIT
from app.const import ACTIVE_RIDE_STATUSES, RIDE_REQUEST_REMOVAL_REASONS
from app.crud.ride import ALLOWED_TRANSITIONS, STATUSES
from app.schemas.driver_profile import DriverModerationAction, DriverProfileApproveIn, DriverProfileUpdate, DriverProfileUpdateMe
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
        "driver_profile_resubmitted",
        "driver_assigned_elsewhere",
    }


def test_public_ride_request_update_only_accepts_selection():
    update = RideDriversRequestUpdate(status="accepted")
    assert update.status == "accepted"


def test_public_ride_request_update_rejects_removal_semantics():
    with pytest.raises(ValidationError):
        RideDriversRequestUpdate(status="canceled", removal_reason="driver_offline")


def test_driver_update_classes_are_optional_unique_and_non_empty():
    assert DriverProfileUpdateMe().classes_allowed is None
    assert DriverProfileUpdateMe(classes_allowed=["vip", "light"]).classes_allowed == ["vip", "light"]

    for classes in ([], ["light", "light"], ["comfort"]):
        with pytest.raises(ValidationError):
            DriverProfileUpdateMe(classes_allowed=classes)


def test_admin_approve_requires_non_empty_unique_classes():
    for classes in ([], ["light", "light"]):
        with pytest.raises(ValidationError):
            DriverProfileApproveIn(classes_allowed=classes)


def test_admin_update_requires_non_empty_unique_classes_when_supplied():
    for classes in ([], ["light", "light"]):
        with pytest.raises(ValidationError):
            DriverProfileUpdate(classes_allowed=classes)


def test_moderation_requires_profile_revision():
    with pytest.raises(ValidationError):
        DriverModerationAction(
            status="approved",
            admin_user_id=1,
            classes_allowed=["light"],
        )


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
