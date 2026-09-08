from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorBody, ErrorDetail, ErrorResponse


def error_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    return mapping.get(status_code, "ERROR")


def error_response(status_code: int, message: str, details: list[ErrorDetail] | None = None) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorBody(
            code=error_code(status_code),
            message=message,
            details=details or [],
        )
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(by_alias=True))


def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return error_response(exc.status_code, message)


def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        ErrorDetail(
            field=".".join(str(part) for part in error.get("loc", [])),
            message=str(error.get("msg", "Invalid value")),
        )
        for error in exc.errors()
    ]
    return error_response(422, "Request validation failed", details)


async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return error_response(500, "Internal server error")
