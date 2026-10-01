from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float
    altitude_m: float = 0.0


class MissionState(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    PATROLLING = "patrolling"
    RUNNING = "patrolling"
    PAUSED = "paused"
    RETURNING = "returning"
    COMPLETE = "complete"
    COMPLETED = "complete"
    ABORTED = "aborted"


@dataclass(frozen=True)
class Telemetry:
    position: Coordinate
    battery_percent: float
    battery_voltage: float | None = None
    connected: bool = True


@dataclass(frozen=True)
class MissionConfig:
    return_battery_percent: float = 30.0
    critical_battery_percent: float = 20.0
    minimum_battery_reserve_percent: float = 15.0
    max_route_points: int = 10_000


@dataclass(frozen=True)
class MissionPlan:
    base: Coordinate
    route: tuple[Coordinate, ...]
    source: str


@dataclass
class Mission:
    """Complete mission definition shared by planners and executors."""

    name: str
    plan: MissionPlan
    altitude_m: float = 100.0
    speed_mps: float = 10.0
    survey_spacing_m: float | None = None
    initial_battery_percent: float = 100.0
    id: str = field(default_factory=lambda: f"mission-{uuid4().hex[:12]}")
    state: MissionState = MissionState.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    aborted_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("o nome da missão não pode ser vazio")
        if self.altitude_m <= 0:
            raise ValueError("a altitude deve ser positiva")
        if self.speed_mps <= 0:
            raise ValueError("a velocidade deve ser positiva")
        if self.survey_spacing_m is not None and self.survey_spacing_m <= 0:
            raise ValueError("o espaçamento deve ser positivo")
        if not 0 < self.initial_battery_percent <= 100:
            raise ValueError("a bateria inicial deve estar entre 0 e 100")

    def mark_ready(self) -> None:
        if self.state is not MissionState.DRAFT:
            raise RuntimeError(f"missão não está em rascunho: {self.state.value}")
        self.state = MissionState.READY

    def mark_started(self, when: datetime | None = None) -> None:
        if self.state is not MissionState.READY:
            raise RuntimeError(f"missão não está pronta: {self.state.value}")
        self.state = MissionState.PATROLLING
        self.started_at = when or datetime.now(timezone.utc)

    def mark_finished(self, when: datetime | None = None) -> None:
        if self.state not in {MissionState.PATROLLING, MissionState.RETURNING}:
            raise RuntimeError(f"missão não pode ser concluída: {self.state.value}")
        self.state = MissionState.COMPLETE
        self.completed_at = when or datetime.now(timezone.utc)

    def pause(self) -> None:
        if self.state is not MissionState.PATROLLING:
            raise RuntimeError(f"missão não pode pausar: {self.state.value}")
        self.state = MissionState.PAUSED

    def resume(self) -> None:
        if self.state is not MissionState.PAUSED:
            raise RuntimeError(f"missão não pode retomar: {self.state.value}")
        self.state = MissionState.PATROLLING

    def abort(self, when: datetime | None = None) -> None:
        if self.state in {MissionState.COMPLETE, MissionState.ABORTED}:
            raise RuntimeError(f"missão já encerrada: {self.state.value}")
        self.state = MissionState.ABORTED
        self.aborted_at = when or datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation for the future API/storage layer."""
        value = asdict(self)
        value["state"] = self.state.value
        value["created_at"] = self.created_at.isoformat()
        value["started_at"] = self.started_at.isoformat() if self.started_at else None
        value["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        value["aborted_at"] = self.aborted_at.isoformat() if self.aborted_at else None
        value["plan"]["base"] = asdict(self.plan.base)
        value["plan"]["route"] = [asdict(point) for point in self.plan.route]
        return value
