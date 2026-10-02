from fastapi.testclient import TestClient

from monitoramento.api import create_app


def payload():
    return {
        "name": "API mission",
        "base": {"latitude": 0, "longitude": 0, "altitude_m": 0},
        "route": [
            {"latitude": 0, "longitude": 0.001, "altitude_m": 100},
            {"latitude": 0, "longitude": 0.002, "altitude_m": 100},
        ],
        "initial_battery_percent": 90,
        "drone": {"id": "api-drone", "name": "API Drone", "percent_per_km": 20},
    }


def test_api_mission_lifecycle(tmp_path):
    client = TestClient(create_app(str(tmp_path / "api.db")))
    created = client.post("/missions", json=payload())
    assert created.status_code == 200
    mission_id = created.json()["id"]
    assert client.post(f"/missions/{mission_id}/validate").json()["valid"]
    assert client.post(f"/missions/{mission_id}/start").status_code == 200
    assert client.post(f"/missions/{mission_id}/step", json={"elapsed_seconds": 60}).status_code == 200
    assert client.get(f"/missions/{mission_id}/telemetry").status_code == 200
    assert isinstance(client.get(f"/missions/{mission_id}/alerts").json(), list)
    assert client.post(f"/missions/{mission_id}/pause").status_code == 200
    assert client.post(f"/missions/{mission_id}/resume").status_code == 200
    assert client.post(f"/missions/{mission_id}/abort").json()["state"] == "aborted"


def test_api_environmental_analysis(tmp_path):
    client = TestClient(create_app(str(tmp_path / "analysis.db")))
    response = client.post("/nodes/readings", json={"node_id": "node-1", "latitude": 0, "longitude": 0, "data_type": "vegetation", "measurements": {"vegetation_coverage_percent": 88}, "metadata": {"species": "tapir"}})
    assert response.status_code == 200
    result = client.post("/analyses", json={"analysis": "forest_health", "amount_usdc": 1})
    assert result.status_code == 200
    assert result.json()["proof"]["network"] == "solana-devnet"
    assert result.json()["payment"]["status"] == "confirmed"


def test_api_reloads_mission_after_restart(tmp_path):
    database = str(tmp_path / "restart.db")
    first = TestClient(create_app(database))
    mission_id = first.post("/missions", json=payload()).json()["id"]
    second = TestClient(create_app(database))
    assert second.get(f"/missions/{mission_id}").status_code == 200
    assert second.post(f"/missions/{mission_id}/validate").json()["valid"]


def test_api_route_management():
    client = TestClient(create_app(":memory:"))
    base = {"latitude": 0, "longitude": 0, "altitude_m": 0}
    points = [{"latitude": 0, "longitude": .001, "altitude_m": 100}, {"latitude": 0, "longitude": .002, "altitude_m": 100}]
    created = client.post("/routes/manual", json={"base": base, "points": points})
    assert created.status_code == 200
    edited = client.post("/routes/edit", json={"base": base, "route": points, "index": 1, "point": {"latitude": 0, "longitude": .003, "altitude_m": 100}})
    assert edited.json()["route"][1]["longitude"] == .003
    assert client.post("/routes/export", json={"base": base, "route": points}).json()["geometry"]["type"] == "LineString"


def test_api_fleet_handover(tmp_path):
    client = TestClient(create_app(str(tmp_path / "fleet.db")))
    mission_id = client.post("/missions", json=payload()).json()["id"]
    assert client.post("/fleet/drones", json={"drone_id": "a", "name": "A"}).status_code == 200
    assert client.post("/fleet/drones", json={"drone_id": "b", "name": "B"}).status_code == 200
    assert client.post("/fleet/sector-a/assign", json={"mission_id": mission_id}).json()["drone_id"] == "a"
    handover = client.post("/fleet/sector-a/handover", json={"mission_id": mission_id}).json()
    assert handover == {"covered": True, "incoming_drone_id": "b"}
