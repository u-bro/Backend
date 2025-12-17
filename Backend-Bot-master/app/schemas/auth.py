from pydantic import Field
from . import BaseSchema


class AuthSchemaRegister(BaseSchema):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    phone: str = Field(..., max_length=20)
    username: str | None = Field(None, max_length=100)


class AuthSchemaLogin(BaseSchema):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)


class TokenResponse(BaseSchema):
    access_token: str = Field(...)
    user_id: int = Field(...)


class AuthSchemaLogout(BaseSchema):
    user_id: int = Field(...)
