"""Точка входа AI-модуля. Контракт — docs/api-contract.md, правила — docs/ai-triage-rules.md."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from . import advisor, classifier, detector, ranker
from .types import (
    RankedVictim,
    RawScene,
    SCENE_SIGNAL_LOW_VISIBILITY,
    SUPPORTED_SCENARIOS,
)


__all__ = ["analyze", "SUPPORTED_SCENARIOS"]


_LOW_CONFIDENCE_THRESHOLD = 0.5


def _build_quality(scene: RawScene, confidence: float) -> Dict[str, Any]:
    notes: List[str] = []
    low = confidence < _LOW_CONFIDENCE_THRESHOLD

    if SCENE_SIGNAL_LOW_VISIBILITY in scene.scene_signals:
        notes.append("Низкая видимость в кадре (дым/темнота) — оценка ненадёжна.")
        low = True

    if low and not notes:
        notes.append("Низкая уверенность модели — требуется визуальный осмотр.")

    return {"low_confidence": low, "notes": notes}


def _victim_to_dict(v: RankedVictim) -> Dict[str, Any]:
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


def analyze(scenario: str) -> Dict[str, Any]:
    scene, raw_victims = detector.detect(scenario)
    classified = classifier.classify(scene, raw_victims)
    ranked = ranker.rank(classified)
    risk = ranker.overall_risk(ranked)

    confidence = scene.base_confidence
    quality = _build_quality(scene, confidence)

    actions = advisor.build_recommended_actions(
        scene, ranked, low_confidence=quality["low_confidence"]
    )
    protocols = advisor.used_protocols(
        scene, ranked, low_confidence=quality["low_confidence"]
    )

    return {
        "analysis_id": f"an-{uuid.uuid4().hex[:8]}",
        "overall_risk": risk,
        "confidence": round(confidence, 3),
        "scene": {
            "people_count": scene.people_count,
            "observations": list(scene.observations),
        },
        "victims": [_victim_to_dict(v) for v in ranked],
        "recommended_actions": actions,
        "protocols": protocols,
        "quality": quality,
        "disclaimer": advisor.DISCLAIMER,
        "scenario": scenario,
    }
