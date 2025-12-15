from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import ResponseValidationError

from app.backend.middlewares.exception import setup_error_middleware
from app.backend.openapi_schema import custom_openapi
from app.backend.middlewares import DBSessionMiddleware, TelegramAuthMiddleware
from app.backend.routers import gpu_router, user_router, users_gpus_storage_router, order_router
from app.backend.utils.pg_errs_router import pg_errs_router

app = FastAPI()
app.openapi = lambda: custom_openapi(app)
app.add_middleware(TelegramAuthMiddleware)
app.add_middleware(DBSessionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
setup_error_middleware(app)

app.include_router(gpu_router, tags=['Gpu'])
app.include_router(user_router, tags=['User'])
app.include_router(users_gpus_storage_router, tags=['Gpu storage'])
app.include_router(order_router, tags=['Order'])
app.include_router(pg_errs_router, tags=["Debug"])


@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request: Request, exc: ResponseValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error occurred",
            # "errors": exc.errors(),
            "body": exc.body,
        },
    )


@app.get("/")
async def hello_world():
    return {"message": "Hello, World!"}
