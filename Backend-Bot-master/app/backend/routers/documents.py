from fastapi import Depends, File, HTTPException, Request, UploadFile, Query
from fastapi.responses import Response
from app.backend.deps import require_role, get_current_user_id
from app.backend.routers.base import BaseRouter
from app.models import User
from app.crud import document_crud, ride_crud, driver_profile_crud


class DocumentRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(document_crud, "/documents")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/avatar/{{id}}", self.get_avatar_by_user_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{key:path}}", self.get_by_key, methods=["GET"], status_code=200)
        self.router.add_api_route(f"{self.prefix}/{{key:path}}/url", self.get_public_url, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/avatar", self.upload_avatar, methods=["POST"], status_code=201)
        self.router.add_api_route(f"{self.prefix}/{{key:path}}", self.upload, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{key:path}}", self.delete_by_key, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["admin"]))])

    async def get_by_key(self, request: Request, key: str, download: bool = False, user: User = Depends(require_role(["user", "driver", "admin"]))) -> Response:
        filename = key.split("/")[-1] or "document.pdf"
        path_parts = key.split("/")
        if len(path_parts) >= 4:
            ride_id = int(path_parts[2])
            ride = await ride_crud.get_by_id(request.state.session, ride_id)
            if not ride:
                raise HTTPException(status_code=404, detail="Ride not found")

            driver_profile = await driver_profile_crud.get_by_id(request.state.session, ride.driver_profile_id)
            if not driver_profile:
                raise HTTPException(status_code=404, detail="Driver_profile not found")
            
            if ride.client_id != user.id and driver_profile.user_id != user.id:
                raise HTTPException(status_code=403, detail="Forbidden")
        
        pdf_bytes = await self.model_crud.get_by_key(key)
        disposition = "attachment" if download else "inline"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"{disposition}; filename={filename}"},
        )

    async def get_avatar_by_user_id(self, request: Request, id: int, role_code: str = Query("user"), download: bool = False) -> Response:
        pdf_bytes = await self.model_crud.get_by_key(f"user/{id}/{role_code}/avatar")
        disposition = "attachment" if download else "inline"
        return Response(
            content=pdf_bytes,
            media_type="image/jpeg",
            headers={"Content-Disposition": f"{disposition}; filename=avatar_{id}"},
        )

    async def get_public_url(self, request: Request, key: str) -> dict:
        return {"url": self.model_crud.presigned_get_url(key), "key": key}

    async def upload(self, request: Request, key: str, file: UploadFile = File(...)) -> dict:
        pdf_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"
        await self.model_crud.upload_bytes(key, pdf_bytes, content_type=content_type)
        return {"key": key, "url": self.model_crud.presigned_get_url(key)}

    async def upload_avatar(self, request: Request, role_code: str = Query("user"), file: UploadFile = File(...), user_id = Depends(get_current_user_id)) -> dict:
        pdf_bytes = await file.read()
        key = f"user/{user_id}/{role_code}/avatar"
        content_type = file.content_type or "image/jpeg"
        await self.model_crud.upload_bytes(key, pdf_bytes, content_type=content_type)
        return {"key": key, "url": self.model_crud.presigned_get_url(key)}

    async def delete_by_key(self, request: Request, key: str) -> dict:
        await self.model_crud.delete_by_key(key)
        return {"key": key}


documents_router = DocumentRouter().router
