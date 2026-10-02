"""Deterministic mission simulator used before hardware integration."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .drone import DroneProfile
from .models import Coordinate, Mission, MissionState, Telemetry
from .return_system import IndependentReturnSystem, ReturnDecision, distance_m
from .validator import MissionValidator
from .alerts import Alert, AlertLevel, AlertManager
from .telemetry import FlightState, FlightTelemetry


class EventType(str, Enum):
    MISSION_STARTED = "mission_started"
    WAYPOINT_REACHED = "waypoint_reached"
    RETURN_TRIGGERED = "return_triggered"
    MISSION_COMPLETED = "mission_completed"


@dataclass(frozen=True)
class MissionEvent:
    type: EventType
    message: str
    battery_percent: float
    position: Coordinate
    created_at: datetime


class SimulatedMissionExecutor:
    """Executes one validated mission waypoint by waypoint."""

    def __init__(self, mission: Mission, drone: DroneProfile):
        result = MissionValidator(drone).validate(mission)
        if not result.valid:
            raise ValueError("missão inválida: " + "; ".join(issue.message for issue in result.errors))
        self.mission = mission
        self.drone = drone
        self.return_system = IndependentReturnSystem(mission.plan, drone.battery_model())
        self.position = mission.plan.base
        self.battery_percent = mission.initial_battery_percent
        self.next_route_index = 0
        self.events: list[MissionEvent] = []
        self.telemetry_history: list[FlightTelemetry] = []
        self.alert_manager = AlertManager()
        self.elapsed_seconds = 0.0
        self.communication_lost = False
        self.gps_failed = False
        self.climate_adverse = False
        self.executor_failed = False

    def start(self) -> None:
        self.mission.mark_ready()
        self.mission.mark_started()
        self._event(EventType.MISSION_STARTED, "missão iniciada")

    def step(self, elapsed_seconds: float = 60.0) -> Telemetry:
        if elapsed_seconds <= 0:
            raise ValueError("elapsed_seconds deve ser positivo")
        if self.executor_failed:
            self.mission.state = MissionState.FAILED
            self._alert("EXECUTOR_FAILURE", AlertLevel.EMERGENCY, "executor da missão falhou")
            raise RuntimeError("simulador em falha")
        if self.mission.state not in {MissionState.PATROLLING, MissionState.RETURNING}:
            raise RuntimeError(f"missão não está em execução: {self.mission.state.value}")
        if self.climate_adverse:
            self._alert("ADVERSE_WEATHER", AlertLevel.CRITICAL, "condições climáticas adversas")
            self.mission.state = MissionState.RETURNING
        current_telemetry = self.telemetry
        if self.communication_lost:
            current_telemetry = Telemetry(self.position, self.battery_percent, connected=False)
            self._alert("COMMUNICATION_LOST", AlertLevel.CRITICAL, "telemetria perdida; retorno de segurança")
        if self.gps_failed:
            self._alert("GPS_FAILURE", AlertLevel.CRITICAL, "falha de GPS; missão interrompida")
            self.mission.state = MissionState.FAILED
            raise RuntimeError("GPS indisponível")
        target = self.return_system.target(current_telemetry)
        if target is None and self.next_route_index < len(self.mission.plan.route):
            target = self.mission.plan.route[self.next_route_index]
        if target is None:
            if self.mission.state is MissionState.PATROLLING:
                self.mission.state = MissionState.RETURNING
                self._event(EventType.RETURN_TRIGGERED, "rota concluída; retorno normal à base")
            target = self.mission.plan.base
        travel_distance = distance_m(self.position, target)
        max_distance = self.drone.cruise_speed_mps * elapsed_seconds if self.drone.cruise_speed_mps else travel_distance
        if max_distance < travel_distance:
            ratio = max_distance / travel_distance
            target = Coordinate(
                self.position.latitude + (target.latitude - self.position.latitude) * ratio,
                self.position.longitude + (target.longitude - self.position.longitude) * ratio,
                self.position.altitude_m + (target.altitude_m - self.position.altitude_m) * ratio,
            )
            travel_distance = max_distance
        self.battery_percent -= self.drone.percent_per_km * travel_distance / 1000
        self.position = target
        if self.next_route_index < len(self.mission.plan.route) and self.position == self.mission.plan.route[self.next_route_index]:
            self.next_route_index += 1
        self.elapsed_seconds += elapsed_seconds
        self._record_telemetry()
        status = self.return_system.evaluate(self.telemetry)
        if status.decision is not ReturnDecision.CONTINUE and self.mission.state is MissionState.PATROLLING:
            self.mission.state = MissionState.RETURNING
            self._event(EventType.RETURN_TRIGGERED, "retorno acionado pelo sistema independente")
        if self.position == self.mission.plan.base and self.mission.state is MissionState.RETURNING:
            self.mission.mark_finished()
            self._event(EventType.MISSION_COMPLETED, "missão concluída na base")
        elif self.next_route_index > 0 and self.position == self.mission.plan.route[self.next_route_index - 1]:
            self._event(EventType.WAYPOINT_REACHED, "waypoint alcançado")
        return self.telemetry

    def run(self, max_steps: int = 10_000, elapsed_seconds: float = 60.0) -> tuple[MissionEvent, ...]:
        if self.mission.state is MissionState.DRAFT:
            self.start()
        for _ in range(max_steps):
            if self.mission.state is MissionState.COMPLETE:
                return tuple(self.events)
            self.step(elapsed_seconds)
        raise RuntimeError("simulação excedeu o número máximo de passos")

    @property
    def telemetry(self) -> Telemetry:
        return Telemetry(self.position, max(0.0, self.battery_percent), connected=not self.communication_lost)

    def simulate_failure(self, failure: str) -> None:
        if failure == "communication":
            self.communication_lost = True
        elif failure == "gps":
            self.gps_failed = True
        elif failure == "weather":
            self.climate_adverse = True
        elif failure == "executor":
            self.executor_failed = True
        else:
            raise ValueError(f"falha desconhecida: {failure}")

    def _record_telemetry(self) -> None:
        state = FlightState.RETURNING if self.mission.state is MissionState.RETURNING else FlightState.FLYING
        self.telemetry_history.append(FlightTelemetry(self.position, self.drone.cruise_speed_mps or 0, 0, max(0, self.battery_percent), None, not self.communication_lost, datetime.now(timezone.utc), state))
        if self.battery_percent <= self.return_system.trigger_percent:
            self._alert("BATTERY_LOW", AlertLevel.WARNING, "bateria atingiu o limite de retorno")

    def _alert(self, code: str, level: AlertLevel, message: str) -> Alert:
        return self.alert_manager.emit(code, level, message, self.position)

    def _consume(self, start: Coordinate, target: Coordinate) -> float:
        return distance_m(start, target) / 1000 * self.drone.percent_per_km

    def _event(self, event_type: EventType, message: str) -> None:
        self.events.append(MissionEvent(event_type, message, self.battery_percent, self.position, datetime.now(timezone.utc)))
