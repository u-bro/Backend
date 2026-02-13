from fastapi import HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.routers.base import BaseRouter
from app.crud.car_photo import car_photo_crud
from app.crud.car import car_crud
from app.schemas.car_photo import CarPhotoSchema, CarPhotoCreate, CarPhotoUpdate
from app.backend.deps import require_role, get_current_driver_profile_id
from app.enum import RoleCode


class CarPhotoRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(car_photo_crud, "/car-photos")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role([RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/car/{{id}}", self.get_by_car_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202)

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[CarPhotoSchema]:
        return await self.model_crud.get_paginated(request.state.session, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> CarPhotoSchema:
        return await super().get_by_id(request, id)
    
    async def get_by_car_id(self, request: Request, id: int) -> list[CarPhotoSchema]:
        return await self.model_crud.get_by_car_id(request.state.session, id)

    async def create(self, request: Request, body: CarPhotoCreate) -> CarPhotoSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, id: int, body: CarPhotoUpdate, driver_profile_id: int = Depends(get_current_driver_profile_id)) -> CarPhotoSchema:
        session = request.state.session
        await self._check_permission(session, id, driver_profile_id)
        return await self.model_crud.update(session, id, body)

    async def delete(self, request: Request, id: int, driver_profile_id: int = Depends(get_current_driver_profile_id)):
        session = request.state.session
        await self._check_permission(session, id, driver_profile_id)
        return await self.model_crud.delete(session, id)

    async def _check_permission(session: AsyncSession, id: int, driver_profile_id: int):
        existing = await car_photo_crud.get_by_id(session, id)
        if not existing:
            raise HTTPException(status_code=404, detail='Car photo not found')
        
        car = await car_crud.get_by_id(session, existing.car_id)
        if not car:
            raise HTTPException(status_code=404, detail='Car not found')

        if car.driver_profile_id != driver_profile_id:
            raise HTTPException(status_code=403, detail='Forbidden')

car_photo_router = CarPhotoRouter().router
