"""FastAPI-приложение RescueVisionAI.

Запуск:
    uvicorn backend.main:app --reload

Swagger UI:
    http://localhost:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .config import CORS_ORIGINS, SERVICE_VERSION


def create_app() -> FastAPI:
    app = FastAPI(
        title="RescueVisionAI API",
        version=SERVICE_VERSION,
        description=(
            "AI-ассистент спасателя МЧС. "
            "Контракт API зафиксирован в docs/api-contract.md."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
