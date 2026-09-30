from .models import Coordinate, MissionConfig, MissionPlan, MissionState, Telemetry


class MissionController:
    def __init__(self, plan: MissionPlan, config: MissionConfig | None = None):
        self.plan = plan
        self.config = config or MissionConfig()
        self.state = MissionState.READY
        self.next_index = 0

    def start(self) -> None:
        if self.state is not MissionState.READY:
            raise RuntimeError(f"missão não pode iniciar no estado {self.state.value}")
        self.state = MissionState.PATROLLING

    def update(self, telemetry: Telemetry) -> Coordinate | None:
        if not telemetry.connected:
            self.state = MissionState.RETURNING
        elif telemetry.battery_percent <= self.config.critical_battery_percent:
            self.state = MissionState.RETURNING
        elif telemetry.battery_percent <= self.config.return_battery_percent:
            self.state = MissionState.RETURNING

        if self.state is MissionState.RETURNING:
            return self.plan.base
        if self.state is not MissionState.PATROLLING:
            return None
        if self.next_index >= len(self.plan.route):
            self.state = MissionState.RETURNING
            return self.plan.base
        target = self.plan.route[self.next_index]
        if _close_enough(telemetry.position, target):
            self.next_index += 1
        return self.plan.route[self.next_index] if self.next_index < len(self.plan.route) else self.plan.base

    def mark_landed(self) -> None:
        if self.state is MissionState.RETURNING:
            self.state = MissionState.COMPLETE


def _close_enough(a: Coordinate, b: Coordinate, tolerance_m: float = 5.0) -> bool:
    lat_m = (a.latitude - b.latitude) * 111_320
    lon_m = (a.longitude - b.longitude) * 111_320
    return (lat_m * lat_m + lon_m * lon_m) ** 0.5 <= tolerance_m
