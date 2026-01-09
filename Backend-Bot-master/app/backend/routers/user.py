from fastapi import Request, Depends
from app.crud import user_crud, driver_location_crud
from app.schemas.user import UserSchemaCreate, UserSchema, UserSchemaMe, UserSchemaMeDriver, UserSchemaUpdate, UserSchemaUpdateMe
from app.backend.routers.base import BaseRouter
from app.backend.deps import require_role, get_current_user, get_current_user_id
from app.models import User

class UserRouter(BaseRouter):
    def __init__(self, model_crud, prefix) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/me", self.get_me, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/me", self.update_me, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role("admin"))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role("admin"))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role("admin"))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 2) -> list[UserSchema]:
        return await super().get_paginated(request, page, page_size)

    async def get_count(self, request: Request) -> int:
        return await super().get_count(request)

    async def get_by_id(self, request: Request, id: int) -> UserSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, create_obj: UserSchemaCreate) -> UserSchema:
        return await super().create(request, create_obj)

    async def delete(self, request: Request, id: int) -> int:
        return await self.model_crud.delete(request.state.session, id)

    async def update(self, request: Request, id: int, update_obj: UserSchemaUpdate) -> UserSchema:
        return await super().update(request, id, update_obj)

    async def get_me(self, request: Request, user: User = Depends(get_current_user)) -> UserSchemaMe | UserSchemaMeDriver:
        role_name = user.role.code
        role_name = "user" if role_name == "driver" and (not user.driver_profile or not user.driver_profile.approved) else role_name
        if role_name == "driver":
            driver_location = await driver_location_crud.get_by_driver_profile_id(request.state.session, user.driver_profile.id)
            return UserSchemaMeDriver(**user.__dict__, role_name=role_name, is_active_ride=driver_location.status=='busy')
        return UserSchemaMe(**user.__dict__, role_name=role_name)

    async def update_me(self, request: Request, update_obj: UserSchemaUpdateMe, user_id: int = Depends(get_current_user_id)) -> UserSchema:
        return await self.model_crud.update(request.state.session, user_id, update_obj)

user_router = UserRouter(user_crud, "/users").router
