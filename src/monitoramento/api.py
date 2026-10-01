"""FastAPI surface for the hardware-free mission prototype."""

from .drone import DroneProfile
from .models import Coordinate, Mission
from .reports import mission_report
from .route_manager import export_geojson
from .routes import geojson_route, polygon_survey, recorded_track
from .simulator import SimulatedMissionExecutor
from .storage import MissionRepository
from .validator import MissionValidator


def create_app(database: str = "monitoramento.db"):
    try:
        from fastapi import FastAPI, HTTPException, UploadFile
    except ImportError as exc:
        raise RuntimeError("instale o extra 'web' para usar a API") from exc

    app = FastAPI(title="R.A.M.A. Mission API")
    repository = MissionRepository(database)
    missions: dict[str, Mission] = {}
    executors: dict[str, SimulatedMissionExecutor] = {}

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
        return MissionValidator(executor.drone).validate(mission).__dict__

    @app.post("/missions/{mission_id}/start")
    def start_mission(mission_id: str):
        executor = executors[mission_id]
        executor.start()
        return executor.telemetry.__dict__

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
        mission.state = mission.state.RETURNING
        return mission.to_dict()

    @app.get("/missions/{mission_id}/telemetry")
    def telemetry(mission_id: str):
        return executors[mission_id].telemetry.__dict__

    @app.get("/missions/{mission_id}/events")
    def events(mission_id: str):
        return repository.list_events(mission_id)

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

    @app.get("/missions/{mission_id}/report")
    def report(mission_id: str):
        executor = executors[mission_id]
        return mission_report(executor.mission, tuple(executor.events), executor.battery_percent)

    return app
