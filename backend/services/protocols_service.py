import json
import logging
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from ..config import get_settings
from ..schemas.protocols import Protocol, ProtocolSummary

logger = logging.getLogger(__name__)


def _load_protocols(path: Path) -> dict[str, Protocol]:
    if not path.exists():
        raise RuntimeError(f"protocols.json not found at {path}")

    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"protocols.json is not valid JSON: {exc}") from exc

    # protocols.json содержит общий disclaimer на верхнем уровне —
    # пробрасываем его в каждый протокол, где он не задан явно.
    default_disclaimer = data.get("disclaimer")
    items = data.get("protocols", [])

    result: dict[str, Protocol] = {}
    for item in items:
        if "disclaimer" not in item and default_disclaimer:
            item = {**item, "disclaimer": default_disclaimer}
        try:
            proto = Protocol.model_validate(item)
        except ValidationError as exc:
            raise RuntimeError(
                f"Invalid protocol {item.get('id', '?')!r} in {path}: {exc}"
            ) from exc
        result[proto.id] = proto

    if not result:
        raise RuntimeError(f"protocols.json at {path} contains no protocols")

    logger.info("loaded %d protocols from %s", len(result), path)
    return result


@lru_cache
def _protocols() -> dict[str, Protocol]:
    return _load_protocols(get_settings().protocols_path)


def warmup() -> None:
    _protocols()


def reset_cache() -> None:
    _protocols.cache_clear()


def list_protocols() -> list[ProtocolSummary]:
    return [
        ProtocolSummary(id=p.id, title=p.title, tags=p.tags)
        for p in _protocols().values()
    ]


def get_protocol(protocol_id: str) -> Protocol | None:
    return _protocols().get(protocol_id)
