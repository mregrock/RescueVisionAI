from fastapi.testclient import TestClient

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
