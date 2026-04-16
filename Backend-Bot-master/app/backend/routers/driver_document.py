from fastapi import Request, Depends
from app.backend.routers.base import BaseRouter
from app.crud.driver_document import driver_document_crud, DriverDocumentCrud
from app.schemas.driver_document import DriverDocumentSchema, DriverDocumentCreate, DriverDocumentAdminUpdate, DriverDocumentDriverUpdate, DriverDocumentAdminUpdateIn, DriverDocumentSchemaWithURL
from app.backend.deps import require_role, require_driver_profile_or_admin, get_current_driver_profile_id_without_approve
from app.models import DriverDocument, User
from app.enum import RoleCode
from datetime import datetime, timezone


class DriverDocumentRouter(BaseRouter[DriverDocumentCrud]):
    def __init__(self, model_crud: DriverDocumentCrud, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role([RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/me", self.get_me, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.DRIVER, RoleCode.ADMIN])), Depends(require_driver_profile_or_admin(DriverDocument))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/driver", self.update_driver, methods=["PUT"], status_code=200, dependencies=[Depends(require_role([RoleCode.DRIVER, RoleCode.ADMIN])), Depends(require_driver_profile_or_admin(DriverDocument))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/admin", self.update_admin, methods=["PUT"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role([RoleCode.DRIVER, RoleCode.ADMIN])), Depends(require_driver_profile_or_admin(DriverDocument))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[DriverDocumentSchema]:
        return await self.model_crud.get_paginated(request.state.session, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> DriverDocumentSchema:
        return await super().get_by_id(request, id)

    async def get_me(self, request: Request, driver_profile_id: int = Depends(get_current_driver_profile_id_without_approve)) -> list[DriverDocumentSchemaWithURL]:
        return await self.model_crud.get_by_driver_profile_id(request.state.session, driver_profile_id)

    async def create(self, request: Request, body: DriverDocumentCreate) -> DriverDocumentSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update_driver(self, request: Request, id: int, body: DriverDocumentDriverUpdate) -> DriverDocumentSchema:
        return await self.model_crud.update(request.state.session, id, body)

    async def update_admin(self, request: Request, id: int, body: DriverDocumentAdminUpdateIn, user: User = Depends(require_role([RoleCode.ADMIN]))) -> DriverDocumentSchema:
        return await self.model_crud.update(request.state.session, id, DriverDocumentAdminUpdate(**body.model_dump(), reviewed_by=user.id, reviewed_at=datetime.now(timezone.utc)))

    async def delete(self, request: Request, id: int):
        return await self.model_crud.delete(request.state.session, id)


driver_document_router = DriverDocumentRouter(driver_document_crud, "/driver-documents").router
