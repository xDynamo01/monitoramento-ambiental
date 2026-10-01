import json
from dataclasses import asdict
from pathlib import Path

from .models import Mission
from .simulator import MissionEvent


def mission_report(mission: Mission, events: tuple[MissionEvent, ...], battery_final: float) -> dict:
    return {
        "mission_id": mission.id,
        "mission_name": mission.name,
        "state": mission.state.value,
        "route_source": mission.plan.source,
        "route_points": [asdict(point) for point in mission.plan.route],
        "base": asdict(mission.plan.base),
        "battery_initial_percent": mission.initial_battery_percent,
        "battery_final_percent": battery_final,
        "waypoints_completed": sum(event.type.value == "waypoint_reached" for event in events),
        "events": [
            {"type": event.type.value, "message": event.message, "battery_percent": event.battery_percent, "position": asdict(event.position), "created_at": event.created_at.isoformat()}
            for event in events
        ],
        "termination_reason": events[-1].message if events else "unknown",
    }


def export_report(report: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(report, indent=2), encoding="utf-8")
