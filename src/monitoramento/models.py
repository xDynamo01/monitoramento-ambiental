from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float
    altitude_m: float = 0.0


class MissionState(str, Enum):
    READY = "ready"
    PATROLLING = "patrolling"
    RETURNING = "returning"
    COMPLETE = "complete"
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
