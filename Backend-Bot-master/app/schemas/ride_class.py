"""Canonical service classes and compatibility for pre-minivan clients."""
from typing import Annotated, Literal
from pydantic import BeforeValidator


def normalize_class(value):
    return "vip" if value == "elite" else value


def normalize_classes(value):
    if isinstance(value, list) and "elite" in value:
        return list(dict.fromkeys(normalize_class(item) for item in value))
    return value


RideClassValue = Annotated[Literal["light", "pro", "vip", "minivan"], BeforeValidator(normalize_class)]
RideClasses = Annotated[list[RideClassValue], BeforeValidator(normalize_classes)]
