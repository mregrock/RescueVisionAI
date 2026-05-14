"""Mock-детектор сцены: возвращает blueprint по сценарию."""

from __future__ import annotations

from typing import List, Tuple

from .scenarios import get_blueprint
from .types import RawScene, RawVictim


def detect(scenario: str) -> Tuple[RawScene, List[RawVictim]]:
    blueprint = get_blueprint(scenario)
    return blueprint["scene"], list(blueprint["victims"])
