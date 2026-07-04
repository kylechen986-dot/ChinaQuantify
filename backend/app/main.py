from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.services.monitor_service import shutdown_monitor_scheduler, start_monitor_scheduler


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    def startup() -> None:
        start_monitor_scheduler()

    @app.on_event("shutdown")
    def shutdown() -> None:
        shutdown_monitor_scheduler()

    return app


app = create_app()
