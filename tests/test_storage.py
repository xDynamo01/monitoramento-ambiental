from monitoramento.models import Coordinate, Mission
from monitoramento.routes import recorded_track
from monitoramento.storage import MissionRepository


def test_repository_saves_mission(tmp_path):
    base = Coordinate(0, 0)
    mission = Mission("Stored", recorded_track(base, [Coordinate(0, .001), Coordinate(0, .002)]))
    repository = MissionRepository(tmp_path / "test.db")
    repository.save(mission)
    rows = repository.list_missions()
    repository.close()
    assert rows[0]["id"] == mission.id
    assert rows[0]["state"] == "draft"
