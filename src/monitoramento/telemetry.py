"""Telemetry contracts shared by simulation and future hardware adapters."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

from .models import Coordinate, Telemetry


class FlightState(str, Enum):
    LANDED = "landed"
    TAKING_OFF = "taking_off"
    FLYING = "flying"
    RETURNING = "returning"
    EMERGENCY = "emergency"


@dataclass(frozen=True)
class FlightTelemetry:
    position: Coordinate
    speed_mps: float
    heading_deg: float
    battery_percent: float
    battery_voltage: float | None
    connected: bool
    timestamp: datetime
    flight_state: FlightState

    def as_legacy(self) -> Telemetry:
        return Telemetry(self.position, self.battery_percent, self.battery_voltage, self.connected)


class TelemetryProvider(Protocol):
    def read(self) -> FlightTelemetry: ...


class SimulatedTelemetryProvider:
    def __init__(self, telemetry: FlightTelemetry):
        self._telemetry = telemetry

    def read(self) -> FlightTelemetry:
        return self._telemetry

    def set(self, telemetry: FlightTelemetry) -> None:
        self._telemetry = telemetry


class MavlinkTelemetryProvider:
    """Future adapter boundary; hardware integration is intentionally deferred."""

    def read(self) -> FlightTelemetry:
        raise NotImplementedError("MAVLink será conectado na etapa de hardware")


def initial_telemetry(position: Coordinate, battery_percent: float) -> FlightTelemetry:
    return FlightTelemetry(position, 0.0, 0.0, battery_percent, None, True, datetime.now(timezone.utc), FlightState.LANDED)
