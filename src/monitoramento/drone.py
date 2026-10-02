"""Manual, hardware-agnostic drone profiles."""

from dataclasses import asdict, dataclass
from typing import Any

from .return_system import BatteryModel


@dataclass(frozen=True)
class DroneProfile:
    """Capabilities and measured performance of one physical or simulated drone."""

    id: str
    name: str
    aircraft_type: str = "unknown"
    battery_capacity_mah: float | None = None
    battery_voltage: float | None = None
    percent_per_km: float = 20.0
    reserve_percent: float = 12.0
    emergency_percent: float = 8.0
    takeoff_percent: float = 3.0
    landing_percent: float = 3.0
    wind_margin_percent: float = 5.0
    cruise_speed_mps: float | None = None
    default_altitude_m: float | None = None
    has_gps: bool = True
    has_camera: bool = False
    has_thermal_camera: bool = False

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip():
            raise ValueError("o drone precisa de id e nome")
        if self.percent_per_km <= 0:
            raise ValueError("percent_per_km deve ser positivo")
        if not 0 <= self.emergency_percent <= self.reserve_percent <= 100:
            raise ValueError("reservas de bateria devem estar entre 0 e 100")
        if self.battery_capacity_mah is not None and self.battery_capacity_mah <= 0:
            raise ValueError("a capacidade da bateria deve ser positiva")
        if self.cruise_speed_mps is not None and self.cruise_speed_mps <= 0:
            raise ValueError("a velocidade de cruzeiro deve ser positiva")
        if self.default_altitude_m is not None and self.default_altitude_m < 0:
            raise ValueError("a altitude padrão não pode ser negativa")

    def battery_model(self) -> BatteryModel:
        return BatteryModel(
            percent_per_km=self.percent_per_km,
            reserve_percent=self.reserve_percent,
            emergency_percent=self.emergency_percent,
            takeoff_percent=self.takeoff_percent,
            landing_percent=self.landing_percent,
            wind_margin_percent=self.wind_margin_percent,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DroneProfile":
        return cls(**value)
