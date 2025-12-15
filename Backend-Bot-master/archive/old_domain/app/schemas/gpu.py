from typing import List, Optional
from pydantic import Field
from . import BaseSchema


class GpuSchemaCreate(BaseSchema):
    name: str | None = Field(None, max_length=255)
    income: float | None = Field(None, gt=0)
    price: int | None = Field(None, gt=0)
    rarity: int | None = Field(None, ge=0)
    algorithm_type: str | None = Field(None, max_length=50)
    coin_type: str | None = Field(None, max_length=5)
    is_crafted: bool | None = Field(None)
    gpu_lvl: int | None = Field(None, gt=0)
    image_url: str | None = Field(None, max_length=500)


class GpuSchema(GpuSchemaCreate):
    id: int = Field(..., gt=0)


class GpuGetPaginatedWithFiltersRequest(BaseSchema):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1)
    sort_by: Optional[str] = None
    sort_desc: bool = False
    price_from: Optional[int] = None
    price_to: Optional[int] = None
    income_from: Optional[float] = None
    income_to: Optional[float] = None
    show_crafted: Optional[bool] = None
    rarity: Optional[List[int]] = None
