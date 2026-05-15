import pytest
from fastapi.testclient import TestClient

from backend.schemas.common import Scenario


def _payload(scenario: str = Scenario.single_unconscious.value) -> dict:
    return {
        "incident_id": "inc-test",
        "rescuer_id": "resc-test",
        "scenario": scenario,
    }


@pytest.mark.parametrize("scenario", [s.value for s in Scenario])
def test_analyze_all_scenarios_match_contract(
    client: TestClient, scenario: str
) -> None:
    response = client.post("/api/v1/analyze", json=_payload(scenario))

    assert response.status_code == 200
    body = response.json()

    expected_fields = {
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
    assert expected_fields.issubset(body.keys())
    assert body["scenario"] == scenario
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["overall_risk"] in {"low", "medium", "high", "critical"}


def test_analyze_missing_required_field_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"incident_id": "inc-test", "scenario": "single_unconscious"},
    )

    assert response.status_code == 422


def test_analyze_unknown_scenario_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analyze", json=_payload("totally_unknown_scenario")
    )

    assert response.status_code == 422


def test_analyze_with_optional_fields(client: TestClient) -> None:
    payload = {
        **_payload(),
        "gps": {"lat": 55.7558, "lon": 37.6173},
        "timestamp": "2026-05-14T12:34:56Z",
    }

    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 200


def test_analyze_single_unconscious_is_critical(client: TestClient) -> None:
    response = client.post("/api/v1/analyze", json=_payload("single_unconscious"))

    body = response.json()
    assert body["overall_risk"] == "critical"
    assert len(body["victims"]) == 1
    assert body["victims"][0]["status"] == "Critical"
