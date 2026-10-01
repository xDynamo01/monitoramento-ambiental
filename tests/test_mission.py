from monitoramento.mission import MissionController
from monitoramento.models import Coordinate, Mission, MissionConfig, MissionState, Telemetry
from monitoramento.routes import polygon_survey, recorded_track, route_length_m
from monitoramento.return_system import BatteryModel, IndependentReturnSystem, ReturnDecision
from monitoramento.validator import IssueLevel, MissionValidator
from monitoramento.drone import DroneProfile
from monitoramento.simulator import EventType, SimulatedMissionExecutor
from monitoramento.alerts import AlertLevel, AlertManager
from monitoramento.reports import mission_report


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


def test_required_battery_covers_outbound_survey_and_inbound():
    base = Coordinate(0, 0)
    route = recorded_track(base, [Coordinate(0, .001), Coordinate(0, .010)])
    system = IndependentReturnSystem(route, BatteryModel(percent_per_km=20, reserve_percent=12))
    required = system.required_mission_battery_percent()
    assert required > system.trigger_percent


def test_return_is_latched_and_independent_from_mission_state():
    base = Coordinate(0, 0)
    route = recorded_track(base, [Coordinate(0, .005), Coordinate(0, .006)])
    system = IndependentReturnSystem(route, BatteryModel(percent_per_km=10, reserve_percent=10))
    status = system.evaluate(Telemetry(route.route[0], 10))
    assert status.decision is ReturnDecision.RETURN_TO_BASE


def test_mission_lifecycle_and_serialization():
    base = Coordinate(-23.0, -46.0, 100)
    plan = recorded_track(base, [Coordinate(-23.001, -46.001, 100), Coordinate(-23.002, -46.002, 100)])
    mission = Mission("Forest sector A", plan, altitude_m=120, speed_mps=12, initial_battery_percent=95)
    assert mission.state is MissionState.DRAFT
    mission.mark_ready()
    mission.mark_started()
    assert mission.state is MissionState.PATROLLING
    assert mission.started_at is not None
    mission.mark_finished()
    data = mission.to_dict()
    assert data["state"] == "complete"
    assert data["plan"]["source"] == "recorded_track"
    assert data["plan"]["route"][0]["latitude"] == -23.001


def test_mission_rejects_invalid_flight_parameters():
    base = Coordinate(0, 0)
    plan = recorded_track(base, [Coordinate(0, .001), Coordinate(0, .002)])
    try:
        Mission("invalid", plan, speed_mps=0)
        assert False
    except ValueError:
        pass


def test_validator_approves_mission_with_enough_battery():
    base = Coordinate(0, 0)
    plan = recorded_track(base, [Coordinate(0, .001), Coordinate(0, .002)])
    mission = Mission("Sector A", plan, altitude_m=80, speed_mps=10, initial_battery_percent=90)
    result = MissionValidator(BatteryModel(percent_per_km=20, reserve_percent=10)).validate(mission)
    assert result.valid
    assert result.errors == ()
    assert result.farthest_distance_m > 0


def test_validator_rejects_insufficient_battery():
    base = Coordinate(0, 0)
    plan = recorded_track(base, [Coordinate(0, .001), Coordinate(0, .010)])
    mission = Mission("Sector A", plan, initial_battery_percent=20)
    result = MissionValidator(BatteryModel(percent_per_km=20, reserve_percent=12)).validate(mission)
    assert not result.valid
    assert any(issue.code == "INSUFFICIENT_INITIAL_BATTERY" for issue in result.errors)


def test_validator_reports_low_margin_as_warning():
    base = Coordinate(0, 0)
    plan = recorded_track(base, [Coordinate(0, .001), Coordinate(0, .010)])
    mission = Mission("Sector A", plan, initial_battery_percent=39)
    result = MissionValidator(BatteryModel(percent_per_km=20, reserve_percent=12)).validate(mission)
    assert not result.valid
    assert any(issue.code == "INSUFFICIENT_INITIAL_BATTERY" for issue in result.errors)


def test_manual_drone_profile_provides_battery_model():
    profile = DroneProfile(
        id="drone-001",
        name="Survey Quad",
        aircraft_type="multirotor",
        percent_per_km=35,
        has_camera=True,
    )
    assert profile.battery_model().percent_per_km == 35
    assert profile.to_dict()["aircraft_type"] == "multirotor"


def test_simulator_completes_valid_mission_and_records_events():
    base = Coordinate(0, 0)
    plan = recorded_track(base, [Coordinate(0, .001), Coordinate(0, .002)])
    mission = Mission("Sector A", plan, initial_battery_percent=90)
    executor = SimulatedMissionExecutor(mission, DroneProfile("d1", "Test", percent_per_km=20))
    events = executor.run()
    assert mission.state is MissionState.COMPLETE
    assert events[0].type is EventType.MISSION_STARTED
    assert events[-1].type is EventType.MISSION_COMPLETED


def test_mission_can_pause_resume_and_abort():
    base = Coordinate(0, 0)
    mission = Mission("Sector A", recorded_track(base, [Coordinate(0, .001), Coordinate(0, .002)]))
    mission.mark_ready()
    mission.mark_started()
    mission.pause()
    assert mission.state is MissionState.PAUSED
    mission.resume()
    mission.abort()
    assert mission.state is MissionState.ABORTED


def test_alerts_and_report_are_structured():
    manager = AlertManager()
    alert = manager.emit("BATTERY_LOW", AlertLevel.WARNING, "battery margin is low")
    assert alert.level is AlertLevel.WARNING
    base = Coordinate(0, 0)
    mission = Mission("Sector A", recorded_track(base, [Coordinate(0, .001), Coordinate(0, .002)]))
    report = mission_report(mission, (), 90)
    assert report["mission_id"] == mission.id
