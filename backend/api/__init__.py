from fastapi import APIRouter

from . import analyze, health, protocols

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(analyze.router)
api_router.include_router(protocols.router)
