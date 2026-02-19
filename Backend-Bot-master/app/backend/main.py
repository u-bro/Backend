from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import ResponseValidationError, RequestValidationError
from fastapi.encoders import jsonable_encoder
from app.backend.middlewares.exception import setup_error_middleware
from app.backend.openapi_schema import custom_openapi
from app.backend.middlewares import install_db_middleware
from app.backend.routers import *


app = FastAPI()
app.openapi = lambda: custom_openapi(app)
install_db_middleware(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
setup_error_middleware(app)

API_PREFIX = "/api/v1"

app.include_router(auth_router, tags=['Auth'], prefix=API_PREFIX)
app.include_router(user_router, tags=['Users'], prefix=API_PREFIX)
app.include_router(ride_router, tags=['Rides'], prefix=API_PREFIX)
app.include_router(role_router, tags=['Roles'], prefix=API_PREFIX)
app.include_router(driver_profile_router, tags=['DriverProfiles'], prefix=API_PREFIX)
app.include_router(driver_document_router, tags=['DriverDocuments'], prefix=API_PREFIX)
app.include_router(phone_verification_router, tags=['PhoneVerifications'], prefix=API_PREFIX)
app.include_router(commission_router, tags=['Commissions'], prefix=API_PREFIX)
app.include_router(tariff_plan_router, tags=['TariffPlan'], prefix=API_PREFIX)
app.include_router(matching_ws_router, tags=['Matching(WebSocket)'], prefix=API_PREFIX)
app.include_router(documents_router, tags=['Documents'], prefix=API_PREFIX)
app.include_router(matching_http_router, tags=['Matching(HTTP)'], prefix=API_PREFIX)
app.include_router(chat_http_router, tags=['Chat(HTTP)'], prefix=API_PREFIX)
app.include_router(chat_ws_router, tags=['Chat(WebSocket)'], prefix=API_PREFIX)
app.include_router(driver_rating_router, tags=['DriverRatings'], prefix=API_PREFIX)
app.include_router(ride_status_history_router, tags=['RideStatusHistory'], prefix=API_PREFIX)
app.include_router(in_app_notification_router, tags=['InAppNotifications'], prefix=API_PREFIX)
app.include_router(notification_ws_router, tags=['Notification(WebSocket)'], prefix=API_PREFIX)
app.include_router(device_token_router, tags=['DeviceTokens'], prefix=API_PREFIX)
app.include_router(push_notification_router, tags=['PushNotifications'], prefix=API_PREFIX)
app.include_router(commission_payment_router, tags=['CommissionPayments'], prefix=API_PREFIX)
app.include_router(tochka_webhook_router, tags=['Tochka(Webhooks)'], prefix=API_PREFIX)
app.include_router(ride_drivers_request_router, tags=['RideDriversRequests'], prefix=API_PREFIX)
app.include_router(car_router, tags=['Cars'], prefix=API_PREFIX)
app.include_router(car_photo_router, tags=['CarPhotos'], prefix=API_PREFIX)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Unprocessable content",
        },
    )

@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request: Request, exc: ResponseValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error occurred",
            "body": jsonable_encoder(exc.body),
        },
    )


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.get(f"{API_PREFIX}/health", tags=["General"]) 
async def health():
    return {"status": "ok"}
