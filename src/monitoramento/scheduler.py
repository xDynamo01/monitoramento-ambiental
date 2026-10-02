"""Operational sector scheduler built on top of FleetCoordinator."""

from dataclasses import dataclass
from enum import Enum

from .fleet import FleetCoordinator, FleetDrone, DroneAvailability
from .models import Mission


class SectorState(str, Enum):
    COVERED = "covered"
    WAITING = "waiting"
    HANDOVER = "handover"
    UNCOVERED = "uncovered"


@dataclass
class Sector:
    sector_id: str
    mission: Mission
    state: SectorState = SectorState.UNCOVERED


class CoverageScheduler:
    """Assigns available drones and keeps sectors covered automatically."""

    def __init__(self, fleet: FleetCoordinator):
        self.fleet = fleet
        self.sectors: dict[str, Sector] = {}

    def add_sector(self, sector: Sector) -> None:
        if sector.sector_id in self.sectors:
            raise ValueError(f"setor já cadastrado: {sector.sector_id}")
        self.sectors[sector.sector_id] = sector

    def dispatch(self, sector_id: str) -> FleetDrone | None:
        sector = self.sectors[sector_id]
        try:
            drone = self.fleet.assign(sector_id, sector.mission)
        except RuntimeError:
            sector.state = SectorState.WAITING
            return None
        sector.state = SectorState.COVERED
        return drone

    def handle_return_request(self, sector_id: str) -> FleetDrone | None:
        sector = self.sectors[sector_id]
        sector.state = SectorState.HANDOVER
        incoming = self.fleet.begin_return(sector_id, sector.mission)
        sector.state = SectorState.COVERED if incoming else SectorState.UNCOVERED
        return incoming

    def release_returning_drone(self, drone_id: str) -> None:
        drone = self.fleet.drones[drone_id]
        drone.availability = DroneAvailability.RETURNING
        drone.active_mission_id = None

    def status(self) -> dict[str, str]:
        return {sector_id: sector.state.value for sector_id, sector in self.sectors.items()}
