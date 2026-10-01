"""Deterministic mission simulator used before hardware integration."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .drone import DroneProfile
from .models import Coordinate, Mission, MissionState, Telemetry
from .return_system import IndependentReturnSystem, ReturnDecision, distance_m
from .validator import MissionValidator


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

    def start(self) -> None:
        self.mission.mark_ready()
        self.mission.mark_started()
        self._event(EventType.MISSION_STARTED, "missão iniciada")

    def step(self) -> Telemetry:
        if self.mission.state not in {MissionState.PATROLLING, MissionState.RETURNING}:
            raise RuntimeError(f"missão não está em execução: {self.mission.state.value}")
        target = self.return_system.target(self.telemetry)
        if target is None and self.next_route_index < len(self.mission.plan.route):
            target = self.mission.plan.route[self.next_route_index]
            self.next_route_index += 1
        if target is None:
            if self.mission.state is MissionState.PATROLLING:
                self.mission.state = MissionState.RETURNING
                self._event(EventType.RETURN_TRIGGERED, "rota concluída; retorno normal à base")
            target = self.mission.plan.base
        self.battery_percent -= self._consume(self.position, target)
        self.position = target
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

    def run(self, max_steps: int = 10_000) -> tuple[MissionEvent, ...]:
        if self.mission.state is MissionState.DRAFT:
            self.start()
        for _ in range(max_steps):
            if self.mission.state is MissionState.COMPLETE:
                return tuple(self.events)
            self.step()
        raise RuntimeError("simulação excedeu o número máximo de passos")

    @property
    def telemetry(self) -> Telemetry:
        return Telemetry(self.position, max(0.0, self.battery_percent))

    def _consume(self, start: Coordinate, target: Coordinate) -> float:
        return distance_m(start, target) / 1000 * self.drone.percent_per_km

    def _event(self, event_type: EventType, message: str) -> None:
        self.events.append(MissionEvent(event_type, message, self.battery_percent, self.position, datetime.now(timezone.utc)))
