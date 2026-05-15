from fastapi import APIRouter, HTTPException, status

from ..schemas.protocols import Protocol, ProtocolsList
from ..services import protocols_service

router = APIRouter(tags=["protocols"])


@router.get("/protocols", response_model=ProtocolsList)
def list_protocols_endpoint() -> ProtocolsList:
    return ProtocolsList(protocols=protocols_service.list_protocols())


@router.get("/protocols/{protocol_id}", response_model=Protocol)
def get_protocol_endpoint(protocol_id: str) -> Protocol:
    proto = protocols_service.get_protocol(protocol_id)
    if proto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Protocol not found")
    return proto
