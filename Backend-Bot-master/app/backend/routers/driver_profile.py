from fastapi import Depends, Header, HTTPException, Request
from app.backend.routers.base import BaseRouter
from app.crud.driver_profile import driver_profile_crud, DriverProfileCrud
from app.config import MODERATION_INTERNAL_TOKEN
from app.schemas.driver_profile import DriverModerationAction, DriverProfileSchema, DriverProfileCreate, DriverProfileUpdate, DriverProfileApprove, DriverProfileApproveIn, DriverProfileUpdateMe, DriverProfileWithCars
from app.services.moderation_notifications import send_moderation_notification
from app.backend.deps import require_role, get_current_user_id, get_current_driver_profile_id, get_current_driver_profile_id_without_approve
from app.enum import RoleCode


class DriverProfileRouter(BaseRouter[DriverProfileCrud]):
    def __init__(self, model_crud: DriverProfileCrud, prefix: str) -> None:
        super().__init__(model_crud, prefix)

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/me", self.get_me, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/user/{{id}}", self.get_by_user_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/me", self.update_me, methods=["PUT"], status_code=200, dependencies=[Depends(require_role([RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/me/resubmit", self.resubmit, methods=["POST"], status_code=200, dependencies=[Depends(require_role([RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/approve", self.approve_profile, methods=["PUT"], status_code=200, dependencies=[Depends(require_role([RoleCode.ADMIN]))])
        self.router.add_api_route(f"/internal{self.prefix}/{{id}}/moderation", self.internal_moderate, methods=["POST"], status_code=200)

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[DriverProfileWithCars]:
        return await self.model_crud.get_paginated_with_cars(request.state.session, page, page_size)

    async def get_by_id(self, request: Request, id: int) -> DriverProfileWithCars:
        return await self.model_crud.get_by_id_with_cars(request.state.session, id)

    async def get_by_user_id(self, request: Request, id: int) -> DriverProfileWithCars:
        return await self.model_crud.get_by_user_id_with_cars(request.state.session, id)

    async def create(self, request: Request, body: DriverProfileCreate) -> DriverProfileSchema:
        return await self.model_crud.create(request.state.session, body)

    async def update(self, request: Request, id: int, body: DriverProfileUpdate) -> DriverProfileSchema:
        return await self.model_crud.update(request.state.session, id, body)

    async def delete(self, request: Request, id: int):
        return await self.model_crud.delete(request.state.session, id)

    async def approve_profile(self, request: Request, id: int, body: DriverProfileApproveIn, user_id: int = Depends(get_current_user_id)) -> DriverProfileSchema:
        profile = await self.model_crud.approve(request.state.session, id, DriverProfileApprove(approved_by=user_id, **body.model_dump()))
        if profile.approved:
            await send_moderation_notification(request.state.session, profile.id, "driver_moderation_approved")
        return profile

    async def update_me(self, request: Request, body: DriverProfileUpdateMe, id = Depends(get_current_driver_profile_id_without_approve)) -> DriverProfileSchema:
        return await self.model_crud.update_me(request.state.session, id, body)

    async def resubmit(self, request: Request, id: int = Depends(get_current_driver_profile_id_without_approve)) -> DriverProfileSchema:
        profile = await self.model_crud.resubmit(request.state.session, id)
        await send_moderation_notification(request.state.session, profile.id, "driver_moderation_resubmitted")
        return profile

    async def internal_moderate(
        self,
        request: Request,
        id: int,
        body: DriverModerationAction,
        x_moderation_token: str | None = Header(default=None),
    ) -> DriverProfileSchema:
        if not MODERATION_INTERNAL_TOKEN or x_moderation_token != MODERATION_INTERNAL_TOKEN:
            raise HTTPException(status_code=403, detail="Forbidden")

        profile = await self.model_crud.moderate(
            request.state.session,
            id,
            body.status,
            body.moderation_info_ids,
            body.admin_user_id,
            body.expected_updated_at,
            body.classes_allowed,
        )
        await send_moderation_notification(
            request.state.session,
            profile.id,
            "driver_moderation_approved" if body.status == "approved" else "driver_moderation_rejected",
            body.moderation_info_ids,
        )
        return profile

    async def get_me(self, request: Request, id: int = Depends(get_current_driver_profile_id_without_approve)) -> DriverProfileWithCars:
        return await self.model_crud.get_by_id_with_cars(request.state.session, id)

driver_profile_router = DriverProfileRouter(driver_profile_crud, "/driver-profiles").router
