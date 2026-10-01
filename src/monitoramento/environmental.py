"""Off-chain environmental data ingestion and MVP analyses."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AnalysisType(str, Enum):
    FOREST_HEALTH = "forest_health"
    TERRAIN = "terrain"
    BIODIVERSITY = "biodiversity"


@dataclass(frozen=True)
class EnvironmentalReading:
    node_id: str
    latitude: float
    longitude: float
    data_type: str
    measurements: dict[str, float]
    metadata: dict[str, Any]
    timestamp: datetime

    @classmethod
    def now(cls, node_id: str, latitude: float, longitude: float, data_type: str, measurements: dict[str, float], metadata: dict[str, Any] | None = None):
        return cls(node_id, latitude, longitude, data_type, measurements, metadata or {}, datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


class EnvironmentalStore:
    def __init__(self):
        self.readings: list[EnvironmentalReading] = []

    def ingest(self, reading: EnvironmentalReading) -> EnvironmentalReading:
        if not reading.node_id.strip():
            raise ValueError("node_id é obrigatório")
        if not -90 <= reading.latitude <= 90 or not -180 <= reading.longitude <= 180:
            raise ValueError("localização inválida")
        self.readings.append(reading)
        return reading

    def by_node(self, node_id: str) -> list[EnvironmentalReading]:
        return [item for item in self.readings if item.node_id == node_id]

    def analyze(self, analysis_type: AnalysisType, node_ids: list[str] | None = None) -> dict[str, Any]:
        selected = [item for item in self.readings if not node_ids or item.node_id in node_ids]
        if not selected:
            raise ValueError("não existem dados para análise")
        measurements = [item.measurements for item in selected]
        if analysis_type is AnalysisType.FOREST_HEALTH:
            coverage = _average(measurements, "vegetation_coverage_percent", 0)
            change = _average(measurements, "vegetation_change_percent", 0)
            return {"analysis": analysis_type.value, "vegetation_coverage_percent": coverage, "vegetation_change_percent": change, "readings": len(selected)}
        if analysis_type is AnalysisType.TERRAIN:
            return {"analysis": analysis_type.value, "elevation_m": _average(measurements, "elevation_m", 0), "slope_percent": _average(measurements, "slope_percent", 0), "readings": len(selected)}
        species = sorted({str(item.metadata["species"]) for item in selected if "species" in item.metadata})
        return {"analysis": analysis_type.value, "species_detected": species, "species_count": len(species), "readings": len(selected)}


def _average(measurements: list[dict[str, float]], key: str, default: float) -> float:
    values = [float(item[key]) for item in measurements if key in item]
    return round(sum(values) / len(values), 2) if values else default
