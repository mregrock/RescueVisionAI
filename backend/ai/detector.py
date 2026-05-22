from .scenarios import get_blueprint
from .types import RawScene, RawVictim


def detect(scenario: str) -> tuple[RawScene, list[RawVictim]]:
    blueprint = get_blueprint(scenario)
    return blueprint["scene"], list(blueprint["victims"])


def detect_from_image(image_bytes: bytes) -> tuple[RawScene, list[RawVictim]]:
    from . import triage_model  # noqa: PLC0415
    from .frame_filter import filter_frame  # noqa: PLC0415

    result = filter_frame(image_bytes)

    if not result.is_relevant:
        scene = RawScene(
            people_count=0,
            observations=["Кадр не содержит людей или не читается"],
            scene_signals=["low_visibility"] if result.low_visibility else [],
            base_confidence=0.0,
        )
        return scene, []

    return triage_model.analyze(image_bytes, low_visibility=result.low_visibility)
