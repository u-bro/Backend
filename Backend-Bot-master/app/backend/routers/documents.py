from fastapi import Depends, File, Request, UploadFile
from fastapi.responses import Response
from app.backend.deps import require_role
from app.backend.routers.base import BaseRouter
from app.crud import document_crud


class DocumentRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(document_crud, "/documents")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}/{{key:path}}", self.get_by_key, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{key:path}}/url", self.get_public_url, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{key:path}}", self.upload, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{key:path}}", self.delete_by_key, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["admin"]))])

    async def get_by_key(self, request: Request, key: str, download: bool = False) -> Response:
        pdf_bytes = await self.model_crud.get_by_key(key)
        filename = key.split("/")[-1] or "document.pdf"
        disposition = "attachment" if download else "inline"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"{disposition}; filename={filename}"},
        )

    async def get_public_url(self, request: Request, key: str) -> dict:
        return {"url": self.model_crud.public_url(key), "key": key}

    async def upload(self, request: Request, key: str, file: UploadFile = File(...)) -> dict:
        pdf_bytes = await file.read()
        await self.model_crud.upload_pdf_bytes(key, pdf_bytes)
        return {"key": key, "url": self.model_crud.public_url(key)}

    async def delete_by_key(self, request: Request, key: str) -> dict:
        await self.model_crud.delete_by_key(key)
        return {"key": key}


documents_router = DocumentRouter().router
