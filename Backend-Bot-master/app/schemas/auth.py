from pydantic import Field
from . import BaseSchema
from typing import Literal
from app.enum import RoleCode


class AuthSchemaRegister(BaseSchema):
    phone: str = Field(..., max_length=20)
    role_code: Literal[RoleCode.DRIVER, RoleCode.USER] = Field(...)


class AuthSchemaLogin(BaseSchema):
    phone: str = Field(..., max_length=20)
    code_role: Literal[RoleCode.DRIVER, RoleCode.USER] | None = Field(None)


class TokenResponse(BaseSchema):
    access_token: str = Field(...)
    refresh_token: str = Field(...)


class TokenResponseRegister(TokenResponse):
    is_registred: bool = Field(...)
    

class RefreshTokenVerifyRequest(BaseSchema):
    refresh_token: str = Field(...)
