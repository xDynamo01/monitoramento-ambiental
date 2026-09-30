from dataclasses import dataclass
from math import cos, radians
from pathlib import Path
import json

from .models import Coordinate, MissionPlan


def _coordinate(value: dict) -> Coordinate:
    return Coordinate(float(value["latitude"]), float(value["longitude"]), float(value.get("altitude_m", 0)))


def recorded_track(base: Coordinate, points: list[Coordinate]) -> MissionPlan:
    if len(points) < 2:
        raise ValueError("um trajeto gravado precisa de pelo menos dois pontos")
    return MissionPlan(base, tuple(points), "recorded_track")


def polygon_survey(base: Coordinate, polygon: list[Coordinate], spacing_m: float = 50.0) -> MissionPlan:
    """Gera uma varredura simples leste-oeste dentro do retângulo da área.

    A versão inicial usa o envelope da área para manter o algoritmo previsível;
    a próxima etapa deve recortar as linhas exatamente ao polígono.
    """
    if len(polygon) < 3 or spacing_m <= 0:
        raise ValueError("a área precisa de três pontos e o espaçamento deve ser positivo")
    min_lat = min(p.latitude for p in polygon)
    max_lat = max(p.latitude for p in polygon)
    min_lon = min(p.longitude for p in polygon)
    max_lon = max(p.longitude for p in polygon)
    lat_step = spacing_m / 111_320
    points: list[Coordinate] = []
    row = 0
    lat = min_lat
    while lat <= max_lat + lat_step / 2:
        west = Coordinate(lat, min_lon, polygon[0].altitude_m)
        east = Coordinate(lat, max_lon, polygon[0].altitude_m)
        points.extend((west, east) if row % 2 == 0 else (east, west))
        row += 1
        lat += lat_step
    return MissionPlan(base, tuple(points), "polygon_survey")


def geojson_route(base: Coordinate, path: str | Path) -> MissionPlan:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    geometry = data.get("geometry", data).get("geometry", data.get("geometry", {}))
    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
        if not features:
            raise ValueError("FeatureCollection sem feições")
        geometry = features[0]["geometry"]
    elif data.get("type") == "Feature":
        geometry = data["geometry"]
    coords = geometry.get("coordinates", [])
    if geometry.get("type") != "LineString" or len(coords) < 2:
        raise ValueError("a rota GeoJSON precisa ser uma LineString com dois pontos")
    points = [Coordinate(float(latlon[1]), float(latlon[0])) for latlon in coords]
    return MissionPlan(base, tuple(points), "geojson")
