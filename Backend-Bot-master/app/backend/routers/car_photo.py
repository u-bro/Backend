from fastapi import HTTPException, Request, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.routers.base import BaseRouter
from app.crud.car_photo import car_photo_crud
from app.crud.car import car_crud
from app.crud.document import document_crud
from app.config import S3_AVATARS_BUCKET_UUID
from app.schemas.car_photo import CarPhotoSchema, CarPhotoCreate, CarPhotoUpdate
from app.backend.deps import require_role, get_current_driver_profile_id
from app.enum import RoleCode


class CarPhotoRouter(BaseRouter):
    def __init__(self, model_crud, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role([RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/car/{{id}}", self.get_by_car_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/car/{{id}}/photos/{{photo_id}}/image", self.get_image, methods=["GET"], response_class=RedirectResponse, status_code=307, name="car_photo_image", dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202)

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[CarPhotoSchema]:
        return await self.model_crud.get_paginated(request.state.session, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> CarPhotoSchema:
        return await super().get_by_id(request, id)
    
    @staticmethod
    def _is_storage_url(url: str | None) -> bool:
        return bool(url and url.startswith((
            document_crud.client.meta.endpoint_url.rstrip("/") + "/",
            f"https://{S3_AVATARS_BUCKET_UUID}.selstorage.ru/",
        )))

    async def get_by_car_id(self, request: Request, id: int, response: Response) -> list[CarPhotoSchema]:
        photos = await self.model_crud.get_by_car_id(request.state.session, id)
        response.headers["Vary"] = "User-Agent"
        response.headers["Cache-Control"] = "private, no-store"
        if request.headers.get("user-agent", "").lower().startswith("okhttp/"):
            # Installed Android versions attach their API token on the initial image request.
            # OkHttp drops that header when following a redirect to another origin.
            for photo in photos:
                if self._is_storage_url(photo.photo_url):
                    url = request.url_for("car_photo_image", id=id, photo_id=photo.id)
                    if request.headers.get("x-forwarded-proto") == "https":
                        url = url.replace(scheme="https")
                    photo.photo_url = str(url)
        return photos

    async def get_image(self, request: Request, id: int, photo_id: int) -> RedirectResponse:
        photos = await self.model_crud.get_by_car_id(request.state.session, id)
        for photo in photos:
            if photo.id == photo_id and self._is_storage_url(photo.photo_url):
                return RedirectResponse(photo.photo_url, headers={"Cache-Control": "private, no-store"})
        raise HTTPException(status_code=404, detail="Car photo not found")

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

car_photo_router = CarPhotoRouter(car_photo_crud, "/car-photos").router
