"""Geographic safety checks for mission routes."""

from dataclasses import dataclass

from .models import Coordinate


@dataclass(frozen=True)
class GeofenceResult:
    valid: bool
    violations: tuple[str, ...]


def point_inside(point: Coordinate, polygon: list[Coordinate]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i, current in enumerate(polygon):
        previous = polygon[j]
        if ((current.longitude > point.longitude) != (previous.longitude > point.longitude)):
            crossing = (previous.latitude - current.latitude) * (point.longitude - current.longitude) / (previous.longitude - current.longitude) + current.latitude
            if point.latitude < crossing:
                inside = not inside
        j = i
    return inside


def validate_route(route: tuple[Coordinate, ...], allowed_area: list[Coordinate] | None = None, forbidden_areas: list[list[Coordinate]] | None = None) -> GeofenceResult:
    violations: list[str] = []
    if allowed_area and any(not point_inside(point, allowed_area) for point in route):
        violations.append("ROUTE_OUTSIDE_ALLOWED_AREA")
    if forbidden_areas and any(point_inside(point, area) for point in route for area in forbidden_areas):
        violations.append("ROUTE_CROSSES_FORBIDDEN_AREA")
    return GeofenceResult(not violations, tuple(violations))
