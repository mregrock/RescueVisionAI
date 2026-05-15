from typing import Annotated

from fastapi import APIRouter, Depends

from ..config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Annotated[Settings, Depends(get_settings)]) -> dict:
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.service_version,
    }
