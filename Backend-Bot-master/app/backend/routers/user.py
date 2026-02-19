from fastapi import Request, Depends, HTTPException
from app.crud.user import user_crud, UserCrud
from app.crud import driver_location_crud, ride_crud
from app.schemas.user import UserSchemaCreate, UserSchema, UserSchemaMe, UserSchemaUpdate, UserSchemaUpdateMe
from app.backend.routers.base import BaseRouter
from app.backend.deps import require_role, get_current_user, get_current_user_id
from app.models import User
from app.enum import RoleCode


class UserRouter(BaseRouter[UserCrud]):
    def __init__(self, model_crud: UserCrud, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/me", self.get_me, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/me", self.update_me, methods=["PUT"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(RoleCode.ADMIN))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(RoleCode.ADMIN))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(RoleCode.ADMIN))])

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

    async def get_me(self, request: Request, user: User = Depends(get_current_user)) ->  UserSchemaMe:
        role_name = user.role.code
        if role_name == RoleCode.DRIVER:
            driver_location = await driver_location_crud.get_by_driver_profile_id(request.state.session, user.driver_profile.id)
            is_active_ride = driver_location.status in ['busy', 'waiting_ride'] if driver_location else False
            return UserSchemaMe(**user.__dict__, role_name=role_name, is_active_ride=is_active_ride)

        rides = await ride_crud.get_by_client_id(request.state.session, user.id)
        statuses = [ride.status for ride in rides if ride.status in ['requested', 'waiting_commission', 'accepted', 'on_the_way', 'arrived', 'started']]
        return UserSchemaMe(**user.__dict__, role_name=role_name, is_active_ride=len(statuses) > 0)

    async def update_me(self, request: Request, update_obj: UserSchemaUpdateMe, user_id: int = Depends(get_current_user_id)) -> UserSchema:
        return await self.model_crud.update(request.state.session, user_id, update_obj)

user_router = UserRouter(user_crud, "/users").router
