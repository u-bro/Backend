from fastapi import Request
from starlette.responses import JSONResponse
from datetime import timedelta

from app.crud.auth import CrudAuth
from app.schemas import AuthSchemaRegister, AuthSchemaLogin, TokenResponse, AuthSchemaLogout, UserSchema
from app.models import User
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from app.backend.routers.base import BaseRouter


class AuthRouter(BaseRouter):
    def __init__(self, model_crud: CrudAuth, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/register", self.register, methods=["POST"], status_code=201)
        self.router.add_api_route(f"{self.prefix}/login", self.login, methods=["POST"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/logout", self.logout, methods=["POST"], status_code=200)

    async def register(self, request: Request, register_obj: AuthSchemaRegister) -> TokenResponse:
        user = await self.model_crud.register_user(request.state.session, register_obj)
        
        if user is None:
            return JSONResponse(status_code=400, content={"detail": "User already exists or registration failed"})
        
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
        access_token = self.model_crud.create_access_token(user.id, expires_delta)
        
        return TokenResponse(access_token=access_token, user_id=user.id)

    async def login(self, request: Request, login_obj: AuthSchemaLogin) -> TokenResponse:
        user = await self.model_crud.login_user(request.state.session, login_obj.email, login_obj.password)
        
        if user is None:
            return JSONResponse(status_code=401, content={"detail": "Invalid email or password"})
        
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
        access_token = self.model_crud.create_access_token(user.id, expires_delta)
        
        return TokenResponse(access_token=access_token, user_id=user.id)

    async def logout(self, request: Request, logout_obj: AuthSchemaLogout) -> JSONResponse:
        await self.model_crud.logout_user(request.state.session, logout_obj.user_id)
        return JSONResponse(status_code=200, content={"detail": "Successfully logged out"})


auth_crud = CrudAuth(User, UserSchema, JWT_SECRET_KEY, JWT_ALGORITHM)
auth_router = AuthRouter(auth_crud, "/auth").router
