from pydantic import Field
from . import BaseSchema


class AuthSchemaRegister(BaseSchema):
    phone: str = Field(..., max_length=20)
    username: str | None = Field(None, max_length=100)


class AuthSchemaLogin(BaseSchema):
    phone: str = Field(..., max_length=20)


class TokenResponse(BaseSchema):
    access_token: str = Field(...)
    user_id: int = Field(...)
