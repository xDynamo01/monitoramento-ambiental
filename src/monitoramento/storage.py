"""Small SQLite repository for missions and mission events."""

import json
import sqlite3
from pathlib import Path

from .models import Mission
from .simulator import MissionEvent


class MissionRepository:
    def __init__(self, database: str | Path = "monitoramento.db"):
        self.database = str(database)
        self.connection = sqlite3.connect(self.database, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS missions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mission_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS battery_profiles (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def save(self, mission: Mission) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO missions(id, name, state, payload) VALUES (?, ?, ?, ?)",
            (mission.id, mission.name, mission.state.value, json.dumps(mission.to_dict())),
        )
        self.connection.commit()

    def save_event(self, mission: Mission, event: MissionEvent) -> None:
        self.connection.execute(
            "INSERT INTO mission_events(mission_id, event_type, payload) VALUES (?, ?, ?)",
            (mission.id, event.type.value, json.dumps({
                "message": event.message,
                "battery_percent": event.battery_percent,
                "position": event.position.__dict__,
                "created_at": event.created_at.isoformat(),
            })),
        )
        self.connection.commit()

    def save_telemetry(self, mission: Mission, telemetry: dict) -> None:
        self.connection.execute("INSERT INTO telemetry_logs(mission_id, payload) VALUES (?, ?)", (mission.id, json.dumps(telemetry)))
        self.connection.commit()

    def save_battery_profile(self, profile: dict) -> None:
        self.connection.execute("INSERT OR REPLACE INTO battery_profiles(id, payload) VALUES (?, ?)", (profile["id"], json.dumps(profile)))
        self.connection.commit()

    def list_events(self, mission_id: str) -> list[dict]:
        return [dict(row) for row in self.connection.execute("SELECT event_type, payload FROM mission_events WHERE mission_id = ? ORDER BY id", (mission_id,))]

    def list_missions(self) -> list[dict]:
        return [dict(row) for row in self.connection.execute("SELECT id, name, state, payload FROM missions ORDER BY rowid DESC")]

    def close(self) -> None:
        self.connection.close()
