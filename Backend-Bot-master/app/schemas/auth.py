from pydantic import Field
from . import BaseSchema
from typing import Literal


class AuthSchemaRegister(BaseSchema):
    phone: str = Field(..., max_length=20)
    role_code: Literal['driver', 'user'] = Field(...)


class AuthSchemaLogin(BaseSchema):
    phone: str = Field(..., max_length=20)


class TokenResponse(BaseSchema):
    access_token: str = Field(...)
    refresh_token: str = Field(...)
    

class RefreshTokenVerifyRequest(BaseSchema):
    refresh_token: str = Field(...)
