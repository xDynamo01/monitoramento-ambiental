"""Independent return-to-base safety system.

This module deliberately does not depend on MissionController. It can be fed by
telemetry from a flight controller or a dedicated power monitor and can issue a
return decision even when the mission planner is unavailable.
"""

from dataclasses import dataclass
from enum import Enum
from math import cos, radians, sqrt

from .models import Coordinate, MissionPlan, Telemetry
from .routes import METERS_PER_DEGREE


class ReturnDecision(str, Enum):
    CONTINUE = "continue"
    RETURN_TO_BASE = "return_to_base"
    EMERGENCY = "emergency"


@dataclass(frozen=True)
class BatteryModel:
    """Conservative battery model for a specific aircraft and payload.

    ``percent_per_km`` must come from measured flight tests. It is not safe to
    infer this value from the battery label alone.
    """

    percent_per_km: float
    reserve_percent: float = 10.0
    emergency_percent: float = 8.0

    def __post_init__(self) -> None:
        if self.percent_per_km <= 0:
            raise ValueError("percent_per_km deve ser positivo")
        if not 0 <= self.emergency_percent <= self.reserve_percent:
            raise ValueError("a reserva de emergência deve ser menor que a reserva normal")


@dataclass(frozen=True)
class ReturnStatus:
    decision: ReturnDecision
    trigger_percent: float
    battery_percent: float
    farthest_point: Coordinate
    distance_to_base_m: float


class IndependentReturnSystem:
    """Computes and enforces a dynamic return threshold for a route."""

    def __init__(self, plan: MissionPlan, battery: BatteryModel):
        if not plan.route:
            raise ValueError("a missão precisa conter pelo menos um ponto")
        self.plan = plan
        self.battery = battery
        self.farthest_point = max(plan.route, key=lambda point: distance_m(point, plan.base))
        self.farthest_distance_m = distance_m(self.farthest_point, plan.base)
        self.trigger_percent = self._required_battery_percent(self.farthest_distance_m)
        self._return_latched = False

    def _required_battery_percent(self, distance_to_base_m: float) -> float:
        return_percent = (distance_to_base_m / 1000) * self.battery.percent_per_km
        return min(100.0, return_percent + self.battery.reserve_percent)

    def evaluate(self, telemetry: Telemetry) -> ReturnStatus:
        """Evaluate battery telemetry and latch return once the limit is reached."""
        if not telemetry.connected or telemetry.battery_percent <= self.battery.emergency_percent:
            self._return_latched = True
            decision = ReturnDecision.EMERGENCY
        elif telemetry.battery_percent <= self.trigger_percent:
            self._return_latched = True
            decision = ReturnDecision.RETURN_TO_BASE
        elif self._return_latched:
            decision = ReturnDecision.RETURN_TO_BASE
        else:
            decision = ReturnDecision.CONTINUE
        return ReturnStatus(
            decision=decision,
            trigger_percent=self.trigger_percent,
            battery_percent=telemetry.battery_percent,
            farthest_point=self.farthest_point,
            distance_to_base_m=self.farthest_distance_m,
        )

    def target(self, telemetry: Telemetry) -> Coordinate | None:
        """Return the base only after the independent safety decision triggers."""
        status = self.evaluate(telemetry)
        return self.plan.base if status.decision is not ReturnDecision.CONTINUE else None


def distance_m(first: Coordinate, second: Coordinate) -> float:
    """Estimate horizontal distance between two coordinates in meters."""
    mean_latitude = radians((first.latitude + second.latitude) / 2)
    north = (first.latitude - second.latitude) * METERS_PER_DEGREE
    east = (first.longitude - second.longitude) * METERS_PER_DEGREE * cos(mean_latitude)
    return sqrt(north * north + east * east)
