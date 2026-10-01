from monitoramento.mission import MissionController
from monitoramento.models import Coordinate, MissionConfig, Telemetry, MissionState
from monitoramento.routes import polygon_survey, recorded_track, route_length_m
from monitoramento.return_system import BatteryModel, IndependentReturnSystem, ReturnDecision


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


def test_polygon_route_stays_inside_a_non_rectangular_area():
    base = Coordinate(0, 0)
    area = [Coordinate(0, 0), Coordinate(0, .003), Coordinate(.003, .0015), Coordinate(.003, 0)]
    plan = polygon_survey(base, area, 100)
    assert all(0 <= point.longitude <= .003 for point in plan.route)
    assert route_length_m(plan.route) > 0


def test_route_length_is_zero_for_one_point():
    assert route_length_m([Coordinate(0, 0)]) == 0


def test_return_threshold_uses_farthest_route_point():
    base = Coordinate(0, 0)
    route = recorded_track(base, [Coordinate(0, .001), Coordinate(0, .010)])
    system = IndependentReturnSystem(route, BatteryModel(percent_per_km=20, reserve_percent=12))
    expected = (route.route[-1].longitude * 111_320 / 1000) * 20 + 12
    assert abs(system.trigger_percent - expected) < 0.01
    assert system.farthest_point == route.route[-1]


def test_return_is_latched_and_independent_from_mission_state():
    base = Coordinate(0, 0)
    route = recorded_track(base, [Coordinate(0, .005), Coordinate(0, .006)])
    system = IndependentReturnSystem(route, BatteryModel(percent_per_km=10, reserve_percent=10))
    status = system.evaluate(Telemetry(route.route[0], 10))
    assert status.decision is ReturnDecision.RETURN_TO_BASE
    status = system.evaluate(Telemetry(route.route[0], 95))
    assert status.decision is ReturnDecision.RETURN_TO_BASE
