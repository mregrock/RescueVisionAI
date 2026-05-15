"""Сигналы -> severity_score / severity_label. Правила: docs/ai-triage-rules.md."""

from .types import (
    ClassifiedVictim,
    RawScene,
    RawVictim,
    RISK_CRITICAL,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    SCENE_SIGNAL_WEIGHTS,
    VICTIM_SIGNAL_WEIGHTS,
)

# Пороги перебираются сверху вниз, первый сработавший — победитель.
_THRESHOLDS = (
    (0.80, RISK_CRITICAL),
    (0.50, RISK_HIGH),
    (0.25, RISK_MEDIUM),
)


def score_to_label(score: float) -> str:
    for threshold, label in _THRESHOLDS:
        if score >= threshold:
            return label
    return RISK_LOW


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _scene_delta(scene: RawScene) -> float:
    return sum(SCENE_SIGNAL_WEIGHTS.get(s, 0.0) for s in scene.scene_signals)


def _victim_delta(victim: RawVictim) -> float:
    return sum(VICTIM_SIGNAL_WEIGHTS.get(s, 0.0) for s in victim.signals)


def classify(scene: RawScene, victims: list[RawVictim]) -> list[ClassifiedVictim]:
    scene_bonus = _scene_delta(scene)
    result: list[ClassifiedVictim] = []
    for victim in victims:
        score = _clamp(_victim_delta(victim) + scene_bonus)
        result.append(
            ClassifiedVictim(
                local_id=victim.local_id,
                signals=list(victim.signals),
                bbox=victim.bbox,
                severity_score=round(score, 3),
                severity_label=score_to_label(score),
            )
        )
    return result
