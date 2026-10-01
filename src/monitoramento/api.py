"""Optional FastAPI surface for the mission simulator."""

from .drone import DroneProfile
from .models import Coordinate, Mission
from .routes import recorded_track
from .simulator import SimulatedMissionExecutor
from .storage import MissionRepository


def create_app(database: str = "monitoramento.db"):
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("instale o extra 'web' para usar a API") from exc

    app = FastAPI(title="R.A.M.A. Mission API")
    repository = MissionRepository(database)

    @app.get("/health")
    def health():
        return {"status": "ok", "hardware": "simulation"}

    @app.get("/missions")
    def missions():
        return repository.list_missions()

    @app.post("/missions/simulate")
    def simulate(payload: dict):
        try:
            base = Coordinate(**payload["base"])
            points = [Coordinate(**point) for point in payload["route"]]
            mission = Mission(
                payload["name"],
                recorded_track(base, points),
                altitude_m=payload.get("altitude_m", 100),
                speed_mps=payload.get("speed_mps", 10),
                initial_battery_percent=payload.get("initial_battery_percent", 100),
            )
            drone = DroneProfile.from_dict(payload["drone"])
            executor = SimulatedMissionExecutor(mission, drone)
            events = executor.run()
            repository.save(mission)
            for event in events:
                repository.save_event(mission, event)
            return {"mission": mission.to_dict(), "events": [event.type.value for event in events]}
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app
