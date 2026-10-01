import json

from monitoramento.models import Coordinate
from monitoramento.route_manager import export_geojson, remove_invalid_points
from monitoramento.routes import geojson_route, polygon_survey, recorded_track


def test_geojson_round_trip(tmp_path):
    base = Coordinate(0, 0)
    plan = recorded_track(base, [Coordinate(0, .001), Coordinate(0, .002)])
    path = tmp_path / "route.geojson"
    export_geojson(plan, path)
    loaded = geojson_route(base, path)
    assert loaded.route == plan.route


def test_invalid_points_are_removed():
    points = [Coordinate(0, 0), Coordinate(100, 0), Coordinate(0, 0, -1)]
    assert remove_invalid_points(points) == [points[0]]
