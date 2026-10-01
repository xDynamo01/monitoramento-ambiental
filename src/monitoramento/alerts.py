from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone

from .models import Coordinate


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass(frozen=True)
class Alert:
    code: str
    level: AlertLevel
    message: str
    position: Coordinate | None = None
    created_at: datetime = datetime.now(timezone.utc)


class AlertManager:
    def __init__(self):
        self.alerts: list[Alert] = []

    def emit(self, code: str, level: AlertLevel, message: str, position: Coordinate | None = None) -> Alert:
        alert = Alert(code, level, message, position)
        self.alerts.append(alert)
        return alert

    def all(self) -> tuple[Alert, ...]:
        return tuple(self.alerts)
