from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="Custom API with Telegram init_data authorization",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "TelegramInitData": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Init data from Telegram Web App in JSON format",
        }
    }

    openapi_schema["security"] = [{"TelegramInitData": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema
