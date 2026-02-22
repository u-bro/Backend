from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from typing import Union, Any
from pydantic import ValidationError
from app.logger import logger
from app.const import HTTP_ERROR_MESSAGES


class ErrorHandlingMiddleware:
    def __init__(self, app: FastAPI) -> None:
        self.app = app

    async def __call__(self, request: Request, call_next) -> Union[JSONResponse, Any]:
        try:
            return await call_next(request)
        except (RequestValidationError, ResponseValidationError):
            raise
        except ValidationError as exc:
            logger.error(f"Validation error occurred: {exc}")
            error_messages = HTTP_ERROR_MESSAGES.get(400, ('VALIDATION_ERROR',))
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": error_messages[0]}
            )
        except Exception as exc:
            logger.error(f"Unexpected error occurred: {exc}")
            error_messages = HTTP_ERROR_MESSAGES.get(500, ('UNKNOWN',))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": error_messages[0]}
            )



def setup_error_middleware(app: FastAPI) -> None:
    app.middleware("http")(ErrorHandlingMiddleware(app))
