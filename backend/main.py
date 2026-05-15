from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .config import get_settings
from .services import protocols_service


def create_app() -> FastAPI:
    settings = get_settings()

    # fail-fast: если protocols.json сломан, падаем на старте,
    # а не на первом запросе к /protocols.
    protocols_service.warmup()

    app = FastAPI(title="RescueVisionAI API", version=settings.service_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
