from typing import List
from fastapi import Depends, HTTPException, Request
from app.backend.deps import require_role
from app.backend.routers.base import BaseRouter
from app.crud.device_token import device_token_crud
from app.schemas.device_token import DeviceTokenCreate, DeviceTokenIn, DeviceTokenSchema
from app.models import User


class DeviceTokenRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(device_token_crud, "/device-tokens")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/me", self.get_my_tokens, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/me/{{token}}", self.get_my_token, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/me", self.create_my_token, methods=["POST"], status_code=201)
        self.router.add_api_route(f"{self.prefix}/me/{{token}}", self.delete, methods=["DELETE"], status_code=200)

    async def get_my_tokens(self, request: Request, user: User = Depends(require_role(["user", "driver", "admin"]))) -> List[DeviceTokenSchema]:
        items = await self.model_crud.get_by_user_id(request.state.session, user.id)
        return items

    async def get_my_token(self, request: Request, token: str, user: User = Depends(require_role(["user", "driver", "admin"]))) -> DeviceTokenSchema:
        item = await self.model_crud.get_by_user_id_and_token(request.state.session, user.id, token)
        if not item:
            raise HTTPException(status_code=404, detail="Device token not found")
        return item

    async def create_my_token(self, request: Request, body: DeviceTokenIn, user: User = Depends(require_role(["user", "driver", "admin"]))) -> DeviceTokenSchema:
        return await self.model_crud.create(request.state.session, DeviceTokenCreate(user_id=user.id, token=body.token, platform=body.platform))

    async def delete(self, request: Request, token: str, user: User = Depends(require_role(["user", "driver", "admin"]))) -> DeviceTokenSchema | None:
        return await self.model_crud.delete_by_user_id_and_token(request.state.session, user.id, token)


device_token_router = DeviceTokenRouter().router
