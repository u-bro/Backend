from types import SimpleNamespace

from app.services.new_ride_notifications import (
    build_new_ride_push_data,
    is_matching_driver,
)


def make_ride(**overrides):
    values = {
        "id": 42,
        "ride_class": "light",
        "ride_type": "with_car",
        "pickup_lat": 55.7558,
        "pickup_lng": 37.6176,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def make_driver(**overrides):
    values = {
        "status": "online",
        "latitude": 55.7558,
        "longitude": 37.6176,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def make_profile(**overrides):
    values = {
        "classes_allowed": ["light"],
        "current_car_id": 10,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_matching_driver_uses_status_permit_car_and_radius(monkeypatch):
    monkeypatch.setattr("app.config.MAX_DISTANCE_KM", 30.0)

    assert is_matching_driver(make_driver(), make_profile(), make_ride()) is True
    assert is_matching_driver(make_driver(status="waiting_ride"), make_profile(), make_ride()) is True
    assert is_matching_driver(make_driver(status="offline"), make_profile(), make_ride()) is False
    assert is_matching_driver(make_driver(), make_profile(classes_allowed=["pro"]), make_ride()) is False
    assert is_matching_driver(make_driver(), make_profile(current_car_id=None), make_ride()) is False
    assert is_matching_driver(
        make_driver(latitude=56.2, longitude=37.6176),
        make_profile(),
        make_ride(),
    ) is False


def test_without_car_ride_does_not_require_current_car():
    driver = make_driver()
    profile = make_profile(current_car_id=None)

    assert is_matching_driver(driver, profile, make_ride(ride_type="without_car")) is True


def test_new_ride_push_data_is_mobile_friendly():
    data = build_new_ride_push_data(make_ride(), 4.126)

    assert data == {
        "type": "new_ride",
        "action": "matching_feed",
        "ride_id": "42",
        "pickup_lat": "55.7558",
        "pickup_lng": "37.6176",
        "distance_to_pickup_km": "4.13",
    }
