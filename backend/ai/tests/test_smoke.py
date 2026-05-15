import pytest

from backend.ai import analyze
from backend.ai.types import (
    RISK_CRITICAL,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    SCENARIO_LOW_CONFIDENCE,
    SCENARIO_MULTIPLE_VICTIMS,
    SCENARIO_SEVERE_BLEEDING,
    SCENARIO_SINGLE_UNCONSCIOUS,
    STATUS_CRITICAL,
    STATUS_SERIOUS,
    SUPPORTED_SCENARIOS,
)


TOP_LEVEL_FIELDS = {
    "analysis_id",
    "overall_risk",
    "confidence",
    "scene",
    "victims",
    "recommended_actions",
    "protocols",
    "quality",
    "disclaimer",
    "scenario",
}


@pytest.mark.parametrize("scenario", SUPPORTED_SCENARIOS)
def test_analyze_returns_contract_shape(scenario: str) -> None:
    result = analyze(scenario)

    assert TOP_LEVEL_FIELDS.issubset(result.keys())
    assert isinstance(result["analysis_id"], str)
    assert result["overall_risk"] in {RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL}
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["disclaimer"]

    scene = result["scene"]
    assert isinstance(scene["people_count"], int) and scene["people_count"] >= 0
    assert isinstance(scene["observations"], list)

    for v in result["victims"]:
        assert {"id", "priority", "severity_score", "severity_label",
                "status", "bbox", "signals", "first_aid", "protocols"}.issubset(v.keys())
        assert 0.0 <= v["severity_score"] <= 1.0
        assert v["priority"] >= 1

    assert isinstance(result["recommended_actions"], list)
    assert isinstance(result["protocols"], list)
    assert isinstance(result["quality"]["low_confidence"], bool)
    assert isinstance(result["quality"]["notes"], list)


def test_single_unconscious_is_critical() -> None:
    result = analyze(SCENARIO_SINGLE_UNCONSCIOUS)

    assert result["overall_risk"] == RISK_CRITICAL
    assert len(result["victims"]) == 1
    assert result["victims"][0]["status"] == STATUS_CRITICAL
    assert result["victims"][0]["priority"] == 1

    action_ids = {a["id"] for a in result["recommended_actions"]}
    assert "ensure_safety" in action_ids
    assert "start_bls" in action_ids
    assert "basic_life_support" in result["protocols"]


def test_severe_bleeding_triggers_bleeding_protocol() -> None:
    result = analyze(SCENARIO_SEVERE_BLEEDING)

    assert result["overall_risk"] in {RISK_HIGH, RISK_CRITICAL}
    action_ids = {a["id"] for a in result["recommended_actions"]}
    assert "stop_bleeding" in action_ids
    assert "severe_bleeding" in result["protocols"]
    assert result["victims"][0]["status"] in {STATUS_SERIOUS, STATUS_CRITICAL}


def test_multiple_victims_triggers_mass_triage() -> None:
    result = analyze(SCENARIO_MULTIPLE_VICTIMS)

    assert result["scene"]["people_count"] >= 2
    assert len(result["victims"]) >= 2

    priorities = [v["priority"] for v in result["victims"]]
    assert priorities == list(range(1, len(priorities) + 1))

    action_ids = {a["id"] for a in result["recommended_actions"]}
    assert "mass_triage" in action_ids
    assert "mass_casualty_triage" in result["protocols"]


def test_low_confidence_marks_quality() -> None:
    result = analyze(SCENARIO_LOW_CONFIDENCE)

    assert result["quality"]["low_confidence"] is True
    assert result["confidence"] < 0.5

    action_ids = {a["id"] for a in result["recommended_actions"]}
    assert "low_confidence_warning" in action_ids


def test_unknown_scenario_raises() -> None:
    with pytest.raises(ValueError):
        analyze("totally_unknown_scenario")


def test_victims_sorted_by_priority() -> None:
    for scenario in SUPPORTED_SCENARIOS:
        result = analyze(scenario)
        priorities = [v["priority"] for v in result["victims"]]
        assert priorities == sorted(priorities), scenario


def test_disclaimer_is_safe() -> None:
    text = analyze(SCENARIO_SINGLE_UNCONSCIOUS)["disclaimer"].lower()
    assert "вспомогательн" in text or "не заменяет" in text
