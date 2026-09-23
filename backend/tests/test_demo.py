def test_seeded_scenario_has_exact_day_one_counts(client):
    response = client.get("/api/v1/demo/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["airports"] == 6
    assert payload["flights"] == 20
    assert payload["passengers"] == 50
    assert payload["bookings"] == 50
    assert payload["disruptions"] == 1
    assert payload["affected_passengers"] == 12
    assert payload["cancelled_flight"]["flight_number"] == "ANV101"
    assert payload["cancelled_flight"]["origin_code"] == "DFW"
    assert payload["cancelled_flight"]["destination_code"] == "LAX"


def test_affected_passenger_detection_preserves_demo_constraints(client):
    response = client.get("/api/v1/disruptions/1/affected-passengers")

    assert response.status_code == 200
    passengers = response.json()
    assert len(passengers) == 12
    assert all(item["synthetic_ref"].startswith("SYN-P") for item in passengers)
    assert {item["group_code"] for item in passengers} == {
        "GRP-001",
        "GRP-002",
        "GRP-003",
        "GRP-004",
        "GRP-005",
    }
    assert sum(item["cabin"] == "BUSINESS" for item in passengers) == 2
    assert sum(item["accessibility_needs"] is not None for item in passengers) == 2


def test_missing_disruption_returns_clear_404(client):
    response = client.get("/api/v1/disruptions/999/affected-passengers")

    assert response.status_code == 404
    assert response.json()["detail"] == "Disruption not found"


def test_reset_is_deterministic_and_audited(client):
    first = client.post("/api/v1/demo/reset")
    second = client.post("/api/v1/demo/reset")
    audit = client.get("/api/v1/audit-logs")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["affected_passengers"] == 12
    assert second.json()["affected_passengers"] == 12
    assert audit.status_code == 200
    assert audit.json()[0]["action"] == "DEMO_SCENARIO_RESET"
    assert "SYNTHETIC" in audit.json()[0]["details_json"]
