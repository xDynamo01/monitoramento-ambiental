"""Route import, editing, and GeoJSON export helpers."""

import json
from pathlib import Path

from .models import Coordinate, MissionPlan
from .routes import geojson_route, recorded_track, polygon_survey


def export_geojson(plan: MissionPlan, path: str | Path) -> None:
    data = {"type": "Feature", "properties": {"source": plan.source}, "geometry": {"type": "LineString", "coordinates": [[point.longitude, point.latitude, point.altitude_m] for point in plan.route]}}
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def remove_invalid_points(points: list[Coordinate]) -> list[Coordinate]:
    return [point for point in points if -90 <= point.latitude <= 90 and -180 <= point.longitude <= 180 and point.altitude_m >= 0]


def replace_point(plan: MissionPlan, index: int, point: Coordinate) -> MissionPlan:
    points = list(plan.route)
    if index < 0 or index >= len(points):
        raise IndexError("índice de waypoint inválido")
    points[index] = point
    return MissionPlan(plan.base, tuple(points), plan.source)
