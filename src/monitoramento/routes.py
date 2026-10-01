"""Route inputs and deterministic survey-route generation.

All public functions return the same :class:`MissionPlan`, so the flight
executor does not need to know how a route was created.
"""

import json
from math import cos, radians, sqrt
from pathlib import Path

from .models import Coordinate, MissionPlan

METERS_PER_DEGREE = 111_320.0


def _validate_coordinate(point: Coordinate) -> None:
    if not -90 <= point.latitude <= 90:
        raise ValueError(f"latitude fora do intervalo: {point.latitude}")
    if not -180 <= point.longitude <= 180:
        raise ValueError(f"longitude fora do intervalo: {point.longitude}")
    if point.altitude_m < 0:
        raise ValueError("altitude não pode ser negativa")


def _validate_base(base: Coordinate) -> None:
    _validate_coordinate(base)


def recorded_track(base: Coordinate, points: list[Coordinate]) -> MissionPlan:
    """Create a route from points captured during a manual flight."""
    _validate_base(base)
    if len(points) < 2:
        raise ValueError("um trajeto gravado precisa de pelo menos dois pontos")
    for point in points:
        _validate_coordinate(point)
    return MissionPlan(base, tuple(points), "recorded_track")


def _horizontal_intersections(latitude: float, polygon: list[Coordinate]) -> list[float]:
    """Return longitude intersections for a horizontal scan line."""
    intersections: list[float] = []
    for first, second in zip(polygon, polygon[1:] + polygon[:1]):
        if first.latitude == second.latitude:
            continue
        low, high = sorted((first.latitude, second.latitude))
        if low <= latitude < high:
            ratio = (latitude - first.latitude) / (second.latitude - first.latitude)
            intersections.append(first.longitude + ratio * (second.longitude - first.longitude))
    return sorted(intersections)


def polygon_survey(base: Coordinate, polygon: list[Coordinate], spacing_m: float = 50.0) -> MissionPlan:
    """Generate a lawnmower survey route clipped to the polygon.

    The route scans west-to-east and east-to-west on alternating rows. The
    polygon is treated as latitude/longitude coordinates over a small area;
    this is appropriate for the first MVP and avoids adding GIS dependencies.
    """
    _validate_base(base)
    if len(polygon) < 3:
        raise ValueError("a área precisa de pelo menos três pontos")
    if spacing_m <= 0:
        raise ValueError("o espaçamento deve ser positivo")
    for point in polygon:
        _validate_coordinate(point)

    min_lat = min(point.latitude for point in polygon)
    max_lat = max(point.latitude for point in polygon)
    latitude_step = spacing_m / METERS_PER_DEGREE
    altitude = polygon[0].altitude_m
    route: list[Coordinate] = []
    row = 0
    latitude = min_lat
    while latitude <= max_lat + latitude_step / 2:
        intersections = _horizontal_intersections(latitude, polygon)
        for start in range(0, len(intersections) - 1, 2):
            west, east = intersections[start], intersections[start + 1]
            segment = (Coordinate(latitude, west, altitude), Coordinate(latitude, east, altitude))
            route.extend(segment if row % 2 == 0 else segment[::-1])
            row += 1
        latitude += latitude_step

    if len(route) < 2:
        raise ValueError("a área não permite gerar uma rota com esse espaçamento")
    return MissionPlan(base, tuple(route), "polygon_survey")


def _extract_geometry(data: dict) -> dict:
    if data.get("type") == "Feature":
        return data.get("geometry", {})
    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
        if len(features) != 1:
            raise ValueError("a FeatureCollection da rota deve conter exatamente uma feição")
        return features[0].get("geometry", {})
    return data


def geojson_route(base: Coordinate, path: str | Path) -> MissionPlan:
    """Load a drawn/georeferenced LineString route from GeoJSON."""
    _validate_base(base)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    geometry = _extract_geometry(data)
    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") != "LineString" or len(coordinates) < 2:
        raise ValueError("a rota GeoJSON precisa ser uma LineString com dois pontos")
    points = []
    for coordinate in coordinates:
        if len(coordinate) < 2:
            raise ValueError("coordenada GeoJSON inválida")
        altitude = float(coordinate[2]) if len(coordinate) > 2 else 0.0
        points.append(Coordinate(float(coordinate[1]), float(coordinate[0]), altitude))
    return MissionPlan(base, tuple(points), "geojson")


def route_length_m(route: tuple[Coordinate, ...] | list[Coordinate]) -> float:
    """Estimate route length in meters using a local equirectangular model."""
    if len(route) < 2:
        return 0.0
    total = 0.0
    for first, second in zip(route, route[1:]):
        mean_latitude = radians((first.latitude + second.latitude) / 2)
        north = (second.latitude - first.latitude) * METERS_PER_DEGREE
        east = (second.longitude - first.longitude) * METERS_PER_DEGREE * cos(mean_latitude)
        total += sqrt(north * north + east * east)
    return total
