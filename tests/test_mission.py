from monitoramento.mission import MissionController
from monitoramento.models import Coordinate, MissionConfig, Telemetry, MissionState
from monitoramento.routes import polygon_survey, recorded_track


def test_recorded_track_requires_two_points():
    base = Coordinate(0, 0)
    try:
        recorded_track(base, [base])
        assert False
    except ValueError:
        pass


def test_low_battery_returns_to_base():
    base = Coordinate(-23.0, -46.0)
    plan = recorded_track(base, [Coordinate(-23.001, -46.001), Coordinate(-23.002, -46.002)])
    controller = MissionController(plan, MissionConfig(return_battery_percent=30))
    controller.start()
    target = controller.update(Telemetry(plan.route[0], 29))
    assert target == base
    assert controller.state is MissionState.RETURNING


def test_polygon_creates_alternating_survey_rows():
    base = Coordinate(0, 0)
    area = [Coordinate(0, 0), Coordinate(0, .001), Coordinate(.002, .001), Coordinate(.002, 0)]
    plan = polygon_survey(base, area, 100)
    assert len(plan.route) > 2
    assert plan.route[0].longitude < plan.route[1].longitude
    assert plan.route[2].longitude > plan.route[3].longitude
