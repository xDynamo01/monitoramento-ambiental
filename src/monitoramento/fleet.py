"""Fleet coordination for continuous sector coverage."""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone

from .models import Mission


class DroneAvailability(str, Enum):
    AVAILABLE = "available"
    PATROLLING = "patrolling"
    RETURNING = "returning"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


@dataclass
class FleetDrone:
    drone_id: str
    name: str
    availability: DroneAvailability = DroneAvailability.AVAILABLE
    active_mission_id: str | None = None
    battery_percent: float = 100.0
    charging_started_at: datetime | None = None


@dataclass(frozen=True)
class CoverageHandover:
    sector_id: str
    outgoing_drone_id: str
    incoming_drone_id: str
    mission_id: str
    created_at: datetime


class FleetCoordinator:
    """Keeps one active drone assigned to each sector when possible."""

    def __init__(self):
        self.drones: dict[str, FleetDrone] = {}
        self.sector_assignments: dict[str, str] = {}
        self.handovers: list[CoverageHandover] = []

    def register(self, drone: FleetDrone) -> None:
        if drone.drone_id in self.drones:
            raise ValueError(f"drone já cadastrado: {drone.drone_id}")
        if not 0 <= drone.battery_percent <= 100:
            raise ValueError("bateria deve estar entre 0 e 100")
        self.drones[drone.drone_id] = drone

    def assign(self, sector_id: str, mission: Mission, preferred_drone_id: str | None = None) -> FleetDrone:
        if sector_id in self.sector_assignments:
            raise RuntimeError(f"setor já possui cobertura: {sector_id}")
        drone = self._select_available(preferred_drone_id)
        if drone is None:
            raise RuntimeError("nenhum drone disponível para assumir o setor")
        drone.availability = DroneAvailability.PATROLLING
        drone.active_mission_id = mission.id
        self.sector_assignments[sector_id] = drone.drone_id
        return drone

    def begin_return(self, sector_id: str, mission: Mission) -> FleetDrone | None:
        outgoing_id = self.sector_assignments.get(sector_id)
        if outgoing_id is None:
            raise KeyError(f"setor sem cobertura: {sector_id}")
        outgoing = self.drones[outgoing_id]
        outgoing.availability = DroneAvailability.RETURNING
        outgoing.active_mission_id = mission.id
        incoming = self._select_available()
        if incoming is None:
            return None
        incoming.availability = DroneAvailability.PATROLLING
        incoming.active_mission_id = mission.id
        self.sector_assignments[sector_id] = incoming.drone_id
        self.handovers.append(CoverageHandover(sector_id, outgoing_id, incoming.drone_id, mission.id, datetime.now(timezone.utc)))
        return incoming

    def start_charging(self, drone_id: str) -> None:
        drone = self.drones[drone_id]
        drone.availability = DroneAvailability.CHARGING
        drone.active_mission_id = None
        drone.charging_started_at = datetime.now(timezone.utc)

    def finish_charging(self, drone_id: str, battery_percent: float = 100.0) -> None:
        if not 0 <= battery_percent <= 100:
            raise ValueError("bateria deve estar entre 0 e 100")
        drone = self.drones[drone_id]
        if drone.availability is not DroneAvailability.CHARGING:
            raise RuntimeError("drone não está em recarga")
        drone.availability = DroneAvailability.AVAILABLE
        drone.battery_percent = battery_percent
        drone.charging_started_at = None

    def coverage(self, sector_id: str) -> FleetDrone | None:
        drone_id = self.sector_assignments.get(sector_id)
        return self.drones.get(drone_id) if drone_id else None

    def _select_available(self, preferred_drone_id: str | None = None) -> FleetDrone | None:
        if preferred_drone_id:
            preferred = self.drones.get(preferred_drone_id)
            if preferred and preferred.availability is DroneAvailability.AVAILABLE:
                return preferred
        return next((drone for drone in self.drones.values() if drone.availability is DroneAvailability.AVAILABLE), None)
