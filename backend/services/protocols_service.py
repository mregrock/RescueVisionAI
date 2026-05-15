import json
import logging

from ..config import PROTOCOLS_PATH
from ..schemas.protocols import Protocol, ProtocolSummary

logger = logging.getLogger(__name__)


def _load_protocols() -> dict[str, Protocol]:
    if not PROTOCOLS_PATH.exists():
        logger.error("protocols.json not found at %s", PROTOCOLS_PATH)
        return {}

    with PROTOCOLS_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    # protocols.json содержит общий disclaimer на верхнем уровне —
    # пробрасываем его в каждый протокол, где он не задан явно.
    default_disclaimer = data.get("disclaimer")
    result: dict[str, Protocol] = {}
    for item in data.get("protocols", []):
        if "disclaimer" not in item and default_disclaimer:
            item = {**item, "disclaimer": default_disclaimer}
        proto = Protocol.model_validate(item)
        result[proto.id] = proto

    logger.info("loaded %d protocols", len(result))
    return result


_PROTOCOLS = _load_protocols()


def list_protocols() -> list[ProtocolSummary]:
    return [ProtocolSummary(id=p.id, title=p.title, tags=p.tags) for p in _PROTOCOLS.values()]


def get_protocol(protocol_id: str) -> Protocol | None:
    return _PROTOCOLS.get(protocol_id)
