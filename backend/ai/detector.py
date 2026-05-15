from .scenarios import get_blueprint
from .types import RawScene, RawVictim


def detect(scenario: str) -> tuple[RawScene, list[RawVictim]]:
    blueprint = get_blueprint(scenario)
    return blueprint["scene"], list(blueprint["victims"])
