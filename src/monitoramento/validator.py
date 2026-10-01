"""Pre-flight validation for missions before execution."""

from dataclasses import dataclass
from enum import Enum

from .models import Mission, MissionConfig
from .drone import DroneProfile
from .return_system import BatteryModel, IndependentReturnSystem
from .routes import route_length_m


class IssueLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    level: IssueLevel


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    issues: tuple[ValidationIssue, ...]
    route_length_m: float
    farthest_distance_m: float
    return_trigger_percent: float

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.level is IssueLevel.ERROR)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.level is IssueLevel.WARNING)


class MissionValidator:
    """Validate a mission using the same battery model used by return safety."""

    def __init__(
        self,
        battery: BatteryModel | DroneProfile,
        config: MissionConfig | None = None,
    ):
        self.battery = battery.battery_model() if isinstance(battery, DroneProfile) else battery
        self.config = config or MissionConfig()

    def validate(self, mission: Mission) -> ValidationResult:
        issues: list[ValidationIssue] = []
        route = mission.plan.route
        route_length = route_length_m(route)

        if len(route) < 2:
            issues.append(self._error("ROUTE_TOO_SHORT", "a rota precisa de pelo menos dois pontos"))
        if len(route) > self.config.max_route_points:
            issues.append(self._error("ROUTE_TOO_LONG", "a rota excede o limite de pontos configurado"))
        if route and route[0] == mission.plan.base:
            issues.append(self._warning("ROUTE_STARTS_AT_BASE", "o primeiro ponto da rota coincide com a base"))

        return_system = IndependentReturnSystem(mission.plan, self.battery)
        trigger = return_system.trigger_percent
        required = return_system.required_mission_battery_percent()
        if mission.initial_battery_percent <= required:
            issues.append(self._error(
                "INSUFFICIENT_INITIAL_BATTERY",
                f"bateria inicial ({mission.initial_battery_percent:.1f}%) não cobre a missão completa ({required:.1f}%)",
            ))
        elif mission.initial_battery_percent <= required + 5:
            issues.append(self._warning(
                "LOW_INITIAL_BATTERY_MARGIN",
                f"margem de autonomia reduzida: {mission.initial_battery_percent - required:.1f}%",
            ))

        if route_length == 0:
            issues.append(self._error("ZERO_ROUTE_DISTANCE", "a distância da rota deve ser maior que zero"))

        return ValidationResult(
            valid=not any(issue.level is IssueLevel.ERROR for issue in issues),
            issues=tuple(issues),
            route_length_m=route_length,
            farthest_distance_m=return_system.farthest_distance_m,
            return_trigger_percent=trigger,
        )

    @staticmethod
    def _error(code: str, message: str) -> ValidationIssue:
        return ValidationIssue(code, message, IssueLevel.ERROR)

    @staticmethod
    def _warning(code: str, message: str) -> ValidationIssue:
        return ValidationIssue(code, message, IssueLevel.WARNING)
