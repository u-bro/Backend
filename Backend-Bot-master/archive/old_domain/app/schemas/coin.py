from pydantic import Field
from . import BaseSchema


class CoinSchemaCreate(BaseSchema):
    name: str | None = Field(None, max_length=255)

    coin_type_multiplier: float | None = Field(None, ge=1)
    algorithm_type_multiplier: float | None = Field(None, ge=1)

    algorithm_type: str | None = Field(None)


class CoinSchema(CoinSchemaCreate):
    id: int = Field(..., gt=0)
