from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.container import AppContainer, build_container
from app.http_errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.routers import analysis, charts, instruments, quotes, signals, snapshots


def create_app(
    settings: Settings | None = None,
    container: AppContainer | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_container = container or build_container(resolved_settings)

    app = FastAPI(
        title="Elite Forex API",
        version="1.0.0",
        description="Elite Forex by Mithuncy. Local signal desk for GOLD, BTC, Silver, US OIL, and EUR/USD.",
    )
    app.state.container = resolved_container
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list(),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
        max_age=600,
    )
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(instruments.router, prefix="/api/v1")
    app.include_router(quotes.router, prefix="/api/v1")
    app.include_router(signals.router, prefix="/api/v1")
    app.include_router(snapshots.router, prefix="/api/v1")
    app.include_router(analysis.router, prefix="/api/v1")
    app.include_router(charts.router, prefix="/api/v1")
    return app


app = create_app()
