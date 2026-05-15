"""Точка входа AI-модуля. Возвращает dict в формате docs/api-contract.md."""

import uuid
from collections.abc import Callable
from typing import Any

from . import advisor, classifier, detector, ranker
from .types import (
    SCENE_SIGNAL_LOW_VISIBILITY,
    SUPPORTED_SCENARIOS,
    RankedVictim,
    RawScene,
)

# когда подключится YOLO/gRPC-клиент — заменим через get_analyzer()
Analyzer = Callable[[str], dict[str, Any]]

__all__ = ["Analyzer", "SUPPORTED_SCENARIOS", "analyze", "get_analyzer"]

_LOW_CONFIDENCE_THRESHOLD = 0.5


def _build_quality(scene: RawScene, confidence: float) -> dict[str, Any]:
    notes: list[str] = []
    low = confidence < _LOW_CONFIDENCE_THRESHOLD

    if SCENE_SIGNAL_LOW_VISIBILITY in scene.scene_signals:
        notes.append("Низкая видимость в кадре (дым/темнота) — оценка ненадёжна.")
        low = True

    if low and not notes:
        notes.append("Низкая уверенность модели — требуется визуальный осмотр.")

    return {"low_confidence": low, "notes": notes}


def _victim_to_dict(v: RankedVictim) -> dict[str, Any]:
    return {
        "id": v.id,
        "priority": v.priority,
        "severity_score": v.severity_score,
        "severity_label": v.severity_label,
        "status": v.status,
        "bbox": v.bbox,
        "signals": v.signals,
        "first_aid": advisor.build_first_aid(v),
        "protocols": advisor.build_victim_protocols(v),
    }


def analyze(scenario: str) -> dict[str, Any]:
    scene, raw_victims = detector.detect(scenario)
    classified = classifier.classify(scene, raw_victims)
    ranked = ranker.rank(classified)

    confidence = scene.base_confidence
    quality = _build_quality(scene, confidence)
    low = quality["low_confidence"]

    return {
        "analysis_id": f"an-{uuid.uuid4().hex[:8]}",
        "overall_risk": ranker.overall_risk(ranked),
        "confidence": round(confidence, 3),
        "scene": {
            "people_count": scene.people_count,
            "observations": list(scene.observations),
        },
        "victims": [_victim_to_dict(v) for v in ranked],
        "recommended_actions": advisor.build_recommended_actions(scene, ranked, low),
        "protocols": advisor.used_protocols(scene, ranked, low),
        "quality": quality,
        "disclaimer": advisor.DISCLAIMER,
        "scenario": scenario,
    }


def get_analyzer() -> Analyzer:
    return analyze
