"""GET /api/v1/health — проверка живости сервиса."""

from fastapi import APIRouter

from ..config import SERVICE_NAME, SERVICE_VERSION

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }
