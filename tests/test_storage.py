from monitoramento.models import Coordinate, Mission
from monitoramento.routes import recorded_track
from monitoramento.storage import MissionRepository
from monitoramento.drone import DroneProfile


def test_repository_saves_mission(tmp_path):
    base = Coordinate(0, 0)
    mission = Mission("Stored", recorded_track(base, [Coordinate(0, .001), Coordinate(0, .002)]))
    repository = MissionRepository(tmp_path / "test.db")
    repository.save(mission)
    rows = repository.list_missions()
    repository.close()
    assert rows[0]["id"] == mission.id
    assert rows[0]["state"] == "draft"


def test_repository_reloads_mission_and_drone_profile(tmp_path):
    database = tmp_path / "reload.db"
    base = Coordinate(0, 0)
    mission = Mission("Reloaded", recorded_track(base, [Coordinate(0, .001), Coordinate(0, .002)]))
    profile = DroneProfile("profile-1", "Generic", percent_per_km=22)
    first = MissionRepository(database)
    first.save(mission)
    first.save_drone_profile(profile, mission.id)
    first.close()
    second = MissionRepository(database)
    restored = second.get_mission(mission.id)
    restored_profile = second.get_drone_profile(mission.id)
    second.close()
    assert restored is not None
    assert restored.plan.route == mission.plan.route
    assert restored_profile is not None
    assert restored_profile.percent_per_km == 22
