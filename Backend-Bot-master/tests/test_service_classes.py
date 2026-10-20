import pytest
from pydantic import TypeAdapter, ValidationError
from app.schemas.ride_class import RideClassValue, RideClasses
from app.schemas.ride import RideSchemaIn, RideSchemaHistory
from app.schemas.driver_profile import DriverProfileUpdateMe, DriverProfileApproveIn


def ride(ride_class, ride_type):
    return RideSchemaIn(pickup_lat=1, pickup_lng=2, dropoff_lat=3, dropoff_lng=4,
                        distance_meters=1000, commission_id=1,
                        ride_class=ride_class, ride_type=ride_type)


@pytest.mark.parametrize('value', ['light', 'pro', 'vip', 'minivan'])
def test_four_classes_accepted(value):
    assert TypeAdapter(RideClassValue).validate_python(value) == value
    assert ride(value, 'with_car').commission_id == 1


def test_legacy_elite_maps_to_vip():
    assert ride('elite', 'with_car').ride_class == 'vip'
    assert RideSchemaHistory(id=1, ride_class='elite').ride_class == 'vip'
    assert TypeAdapter(RideClasses).validate_python(['light', 'elite', 'vip']) == ['light', 'vip']
    assert DriverProfileUpdateMe(current_class='elite', classes_allowed=['vip', 'elite']).classes_allowed == ['vip']
    assert DriverProfileApproveIn(classes_allowed=['elite']).classes_allowed == ['vip']


def test_vip_supports_both_options():
    assert ride('vip', 'with_car').ride_type == 'with_car'
    assert ride('vip', 'without_car').ride_type == 'without_car'


@pytest.mark.parametrize("ride_type", ["without_car", "delivery"])
def test_minivan_requires_driver_vehicle(ride_type):
    with pytest.raises(ValidationError, match='Minivan requires'):
        ride('minivan', ride_type)


def test_invalid_classes_and_duplicates_rejected():
    with pytest.raises(ValidationError):
        TypeAdapter(RideClassValue).validate_python('unknown')
    with pytest.raises(ValidationError):
        DriverProfileUpdateMe(classes_allowed=['minivan', 'minivan'])
