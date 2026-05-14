"""Blueprints для 4 demo-сценариев. Подробнее в docs/ai-triage-rules.md."""

from __future__ import annotations

from typing import Dict

from .types import (
    RawScene,
    RawVictim,
    SCENARIO_LOW_CONFIDENCE,
    SCENARIO_MULTIPLE_VICTIMS,
    SCENARIO_SEVERE_BLEEDING,
    SCENARIO_SINGLE_UNCONSCIOUS,
    SCENE_SIGNAL_LOW_VISIBILITY,
    SCENE_SIGNAL_MULTIPLE_VICTIMS,
    SIGNAL_BLEEDING_VISIBLE,
    SIGNAL_LYING,
    SIGNAL_NO_MOVEMENT,
    SIGNAL_POSSIBLE_UNCONSCIOUS,
    SIGNAL_SEVERE_BLEEDING,
    SIGNAL_SITTING,
    SIGNAL_STANDING,
    SIGNAL_WEAK_MOVEMENT,
    SUPPORTED_SCENARIOS,
)


SCENARIO_BLUEPRINTS: Dict[str, dict] = {
    SCENARIO_SINGLE_UNCONSCIOUS: {
        "scene": RawScene(
            people_count=1,
            observations=[
                "Один пострадавший в кадре",
                "Пострадавший лежит без видимых движений",
                "Видимых преград и опасностей на сцене не обнаружено",
            ],
            scene_signals=[],
            base_confidence=0.85,
        ),
        "victims": [
            RawVictim(
                local_id=1,
                signals=[SIGNAL_LYING, SIGNAL_NO_MOVEMENT, SIGNAL_POSSIBLE_UNCONSCIOUS],
                bbox=[120, 80, 410, 360],
            ),
        ],
    },

    SCENARIO_SEVERE_BLEEDING: {
        "scene": RawScene(
            people_count=1,
            observations=[
                "Один пострадавший в кадре",
                "На одежде/коже видны следы крови",
                "Поза — полусидячая, есть слабые движения",
            ],
            scene_signals=[],
            base_confidence=0.85,
        ),
        "victims": [
            RawVictim(
                local_id=1,
                signals=[SIGNAL_SITTING, SIGNAL_SEVERE_BLEEDING, SIGNAL_WEAK_MOVEMENT],
                bbox=[150, 110, 380, 420],
            ),
        ],
    },

    SCENARIO_MULTIPLE_VICTIMS: {
        "scene": RawScene(
            people_count=3,
            observations=[
                "В кадре несколько пострадавших",
                "Один лежит без движения, другой сидит с признаками травмы",
                "Требуется массовая сортировка",
            ],
            scene_signals=[SCENE_SIGNAL_MULTIPLE_VICTIMS],
            base_confidence=0.70,
        ),
        "victims": [
            RawVictim(local_id=1, signals=[SIGNAL_LYING, SIGNAL_NO_MOVEMENT], bbox=[40, 200, 240, 460]),
            RawVictim(local_id=2, signals=[SIGNAL_SITTING, SIGNAL_BLEEDING_VISIBLE], bbox=[260, 180, 460, 440]),
            RawVictim(local_id=3, signals=[SIGNAL_STANDING, SIGNAL_WEAK_MOVEMENT], bbox=[480, 160, 620, 440]),
        ],
    },

    SCENARIO_LOW_CONFIDENCE: {
        "scene": RawScene(
            people_count=1,
            observations=[
                "Низкая видимость в кадре (дым/темнота)",
                "Контуры пострадавшего читаются плохо",
                "Оценка состояния ненадёжна",
            ],
            scene_signals=[SCENE_SIGNAL_LOW_VISIBILITY],
            base_confidence=0.35,
        ),
        "victims": [
            RawVictim(local_id=1, signals=[SIGNAL_LYING], bbox=None),
        ],
    },
}


def get_blueprint(scenario: str) -> dict:
    if scenario not in SUPPORTED_SCENARIOS:
        raise ValueError(
            f"Unknown scenario: {scenario!r}. Supported: {', '.join(SUPPORTED_SCENARIOS)}"
        )
    return SCENARIO_BLUEPRINTS[scenario]
