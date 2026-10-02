"""FastAPI surface for the hardware-free mission prototype."""

from dataclasses import asdict

from .drone import DroneProfile
from .models import Coordinate, Mission, MissionState
from .reports import mission_report
from .route_manager import export_geojson, remove_invalid_points, replace_point
from .routes import geojson_route, polygon_survey, recorded_track
from .simulator import SimulatedMissionExecutor
from .storage import MissionRepository
from .validator import MissionValidator
from .environmental import AnalysisType, EnvironmentalReading, EnvironmentalStore
from .payments import SimulatedUsdcProvider
from .provenance import SimulatedSolanaProofProvider


def create_app(database: str = "monitoramento.db"):
    try:
        from fastapi import FastAPI, HTTPException, UploadFile
    except ImportError as exc:
        raise RuntimeError("instale o extra 'web' para usar a API") from exc

    app = FastAPI(title="R.A.M.A. Mission API")
    repository = MissionRepository(database)
    missions: dict[str, Mission] = {}
    executors: dict[str, SimulatedMissionExecutor] = {}
    environmental = EnvironmentalStore()
    proof_provider = SimulatedSolanaProofProvider()
    payment_provider = SimulatedUsdcProvider()

    def telemetry_payload(item):
        value = asdict(item) if hasattr(item, "__dataclass_fields__") else dict(item)
        if "timestamp" in value and hasattr(value["timestamp"], "isoformat"):
            value["timestamp"] = value["timestamp"].isoformat()
        if isinstance(value.get("position"), dict):
            value["position"] = dict(value["position"])
        return value

    for row in repository.list_missions():
        mission = repository.get_mission(row["id"])
        if mission:
            profile = repository.get_drone_profile(mission.id)
            if profile:
                missions[mission.id] = mission
                executors[mission.id] = SimulatedMissionExecutor(mission, profile)

    def mission_from_payload(payload: dict) -> tuple[Mission, DroneProfile]:
        base = Coordinate(**payload["base"])
        points = [Coordinate(**point) for point in payload["route"]]
        mission = Mission(payload["name"], recorded_track(base, points), altitude_m=payload.get("altitude_m", 100), speed_mps=payload.get("speed_mps", 10), survey_spacing_m=payload.get("survey_spacing_m"), initial_battery_percent=payload.get("initial_battery_percent", 100))
        return mission, DroneProfile.from_dict(payload["drone"])

    def get_mission(mission_id: str) -> Mission:
        if mission_id not in missions:
            raise HTTPException(status_code=404, detail="missão não encontrada")
        return missions[mission_id]

    @app.get("/health")
    def health():
        return {"status": "ok", "hardware": "simulation"}

    @app.post("/missions")
    def create_mission(payload: dict):
        try:
            mission, drone = mission_from_payload(payload)
            missions[mission.id] = mission
            executors[mission.id] = SimulatedMissionExecutor(mission, drone)
            repository.save(mission)
            repository.save_drone_profile(drone, mission.id)
            return mission.to_dict()
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/missions")
    def list_missions():
        return repository.list_missions()

    @app.get("/missions/{mission_id}")
    def get_mission_data(mission_id: str):
        return get_mission(mission_id).to_dict()

    @app.post("/missions/{mission_id}/validate")
    def validate_mission(mission_id: str):
        mission = get_mission(mission_id)
        executor = executors[mission_id]
        result = MissionValidator(executor.drone).validate(mission)
        return {
            "valid": result.valid,
            "route_length_m": result.route_length_m,
            "farthest_distance_m": result.farthest_distance_m,
            "return_trigger_percent": result.return_trigger_percent,
            "errors": [issue.__dict__ for issue in result.errors],
            "warnings": [issue.__dict__ for issue in result.warnings],
        }

    @app.post("/missions/{mission_id}/start")
    def start_mission(mission_id: str):
        executor = executors[mission_id]
        executor.start()
        return executor.telemetry.__dict__

    @app.post("/missions/{mission_id}/step")
    def step_mission(mission_id: str, payload: dict | None = None):
        executor = executors[mission_id]
        previous_events = len(executor.events)
        telemetry = executor.step(float((payload or {}).get("elapsed_seconds", 60)))
        repository.save(mission := executor.mission)
        repository.save_telemetry(mission, telemetry_payload(telemetry))
        for item in executor.events[previous_events:]:
            repository.save_event(mission, item)
        return {"telemetry": telemetry_payload(telemetry), "state": mission.state.value, "alerts": [alert.__dict__ for alert in executor.alert_manager.all()]}

    @app.post("/missions/{mission_id}/run")
    def run_mission(mission_id: str, payload: dict | None = None):
        executor = executors[mission_id]
        events = executor.run(max_steps=int((payload or {}).get("max_steps", 10_000)), elapsed_seconds=float((payload or {}).get("elapsed_seconds", 60)))
        repository.save(executor.mission)
        for item in events:
            repository.save_event(executor.mission, item)
        for item in executor.telemetry_history:
            repository.save_telemetry(executor.mission, telemetry_payload(item))
        return {"state": executor.mission.state.value, "report": mission_report(executor.mission, events, executor.battery_percent)}

    @app.post("/missions/{mission_id}/failure")
    def inject_failure(mission_id: str, payload: dict):
        executor = executors[mission_id]
        executor.simulate_failure(payload["failure"])
        return {"failure": payload["failure"], "accepted": True}

    @app.post("/missions/{mission_id}/pause")
    def pause_mission(mission_id: str):
        mission = get_mission(mission_id)
        mission.pause()
        return mission.to_dict()

    @app.post("/missions/{mission_id}/resume")
    def resume_mission(mission_id: str):
        mission = get_mission(mission_id)
        mission.resume()
        return mission.to_dict()

    @app.post("/missions/{mission_id}/abort")
    def abort_mission(mission_id: str):
        mission = get_mission(mission_id)
        mission.abort()
        repository.save(mission)
        return mission.to_dict()

    @app.post("/missions/{mission_id}/return")
    def return_mission(mission_id: str):
        mission = get_mission(mission_id)
        mission.state = MissionState.RETURNING
        return mission.to_dict()

    @app.get("/missions/{mission_id}/telemetry")
    def telemetry(mission_id: str):
        executor = executors[mission_id]
        stored = repository.list_telemetry(mission_id)
        return stored or [item.__dict__ for item in executor.telemetry_history] or [executor.telemetry.__dict__]

    @app.get("/missions/{mission_id}/events")
    def events(mission_id: str):
        return repository.list_events(mission_id)

    @app.get("/missions/{mission_id}/alerts")
    def alerts(mission_id: str):
        return [alert.__dict__ for alert in executors[mission_id].alert_manager.all()]

    @app.post("/routes/geojson")
    async def import_geojson(file: UploadFile, base_latitude: float, base_longitude: float):
        path = f".rama-upload-{file.filename}"
        content = await file.read()
        with open(path, "wb") as output:
            output.write(content)
        try:
            plan = geojson_route(Coordinate(base_latitude, base_longitude), path)
            return {"source": plan.source, "route": [point.__dict__ for point in plan.route]}
        finally:
            import os
            os.remove(path)

    @app.post("/routes/survey")
    def create_survey(payload: dict):
        base = Coordinate(**payload["base"])
        polygon = [Coordinate(**point) for point in payload["polygon"]]
        plan = polygon_survey(base, polygon, payload.get("spacing_m", 50))
        return {"source": plan.source, "route": [point.__dict__ for point in plan.route]}

    @app.post("/routes/manual")
    def create_manual_route(payload: dict):
        base = Coordinate(**payload["base"])
        points = [Coordinate(**point) for point in payload["points"]]
        plan = recorded_track(base, remove_invalid_points(points))
        return {"source": plan.source, "route": [point.__dict__ for point in plan.route]}

    @app.post("/routes/edit")
    def edit_route(payload: dict):
        base = Coordinate(**payload["base"])
        original = recorded_track(base, [Coordinate(**point) for point in payload["route"]])
        edited = replace_point(original, int(payload["index"]), Coordinate(**payload["point"]))
        return {"source": edited.source, "route": [point.__dict__ for point in edited.route]}

    @app.post("/routes/clean")
    def clean_route(payload: dict):
        return {"route": [point.__dict__ for point in remove_invalid_points([Coordinate(**point) for point in payload["route"]])]}

    @app.post("/routes/export")
    def export_route(payload: dict):
        base = Coordinate(**payload["base"])
        plan = recorded_track(base, [Coordinate(**point) for point in payload["route"]])
        return {"type": "Feature", "properties": {"source": plan.source}, "geometry": {"type": "LineString", "coordinates": [[point.longitude, point.latitude, point.altitude_m] for point in plan.route]}}

    @app.get("/missions/{mission_id}/report")
    def report(mission_id: str):
        executor = executors[mission_id]
        return mission_report(executor.mission, tuple(executor.events), executor.battery_percent)

    @app.post("/nodes/readings")
    def ingest_reading(payload: dict):
        try:
            reading = EnvironmentalReading.now(payload["node_id"], payload["latitude"], payload["longitude"], payload["data_type"], payload.get("measurements", {}), payload.get("metadata", {}))
            environmental.ingest(reading)
            return reading.to_dict()
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/nodes/readings")
    def list_readings():
        return [reading.to_dict() for reading in environmental.readings]

    @app.post("/analyses")
    def create_analysis(payload: dict):
        try:
            result = environmental.analyze(AnalysisType(payload["analysis"]), payload.get("node_ids"))
            proof = proof_provider.register(result)
            payment = payment_provider.charge(float(payload.get("amount_usdc", 0.01)))
            return {"result": result, "proof": proof.to_dict(), "payment": payment.__dict__}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app
