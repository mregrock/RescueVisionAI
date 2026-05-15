import json

import pytest
from fastapi.testclient import TestClient

from backend.services.protocols_service import _load_protocols

EXPECTED_PROTOCOL_IDS = {
    "scene_safety",
    "primary_assessment",
    "basic_life_support",
    "severe_bleeding",
    "burns",
    "fractures",
    "mass_casualty_triage",
}


def test_list_protocols_returns_all(client: TestClient) -> None:
    response = client.get("/api/v1/protocols")

    assert response.status_code == 200
    items = response.json()["protocols"]
    assert {p["id"] for p in items} == EXPECTED_PROTOCOL_IDS

    for item in items:
        assert {"id", "title", "tags"}.issubset(item.keys())


def test_get_protocol_by_id(client: TestClient) -> None:
    response = client.get("/api/v1/protocols/basic_life_support")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "basic_life_support"
    assert body["steps"]
    assert body["disclaimer"]


def test_get_unknown_protocol_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/protocols/unknown_protocol")

    assert response.status_code == 404
    assert response.json()["detail"] == "Protocol not found"


def test_load_protocols_missing_file_raises(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="not found"):
        _load_protocols(tmp_path / "does_not_exist.json")


def test_load_protocols_invalid_json_raises(tmp_path) -> None:
    bad = tmp_path / "protocols.json"
    bad.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="not valid JSON"):
        _load_protocols(bad)


def test_load_protocols_empty_raises(tmp_path) -> None:
    empty = tmp_path / "protocols.json"
    empty.write_text(json.dumps({"protocols": []}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="no protocols"):
        _load_protocols(empty)


def test_load_protocols_invalid_protocol_raises(tmp_path) -> None:
    bad = tmp_path / "protocols.json"
    bad.write_text(
        json.dumps({"protocols": [{"id": "broken"}]}),  # нет обязательного title
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="Invalid protocol"):
        _load_protocols(bad)
