# db.py
import sqlite3
from typing import Dict, Any, List

DB_PATH = "aqi_history.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    source TEXT,
    location TEXT,
    latitude REAL,
    longitude REAL,
    date_utc TEXT,
    parameter TEXT,
    aqi INTEGER,
    value REAL,
    unit TEXT,
    raw JSON,
    summary TEXT,
    flagged INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_obs_location_date ON observations(location, date_utc);
"""

def get_conn(path: str = DB_PATH):
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

def upsert_observation(obs: Dict[str, Any]):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO observations (id, source, location, latitude, longitude, date_utc, parameter, aqi, value, unit, raw)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, json(?))
    ON CONFLICT(id) DO UPDATE SET
      source=excluded.source,
      location=excluded.location,
      latitude=excluded.latitude,
      longitude=excluded.longitude,
      date_utc=excluded.date_utc,
      parameter=excluded.parameter,
      aqi=excluded.aqi,
      value=excluded.value,
      unit=excluded.unit,
      raw=excluded.raw;
    """, (
        obs["id"],
        obs.get("source"),
        obs.get("location"),
        obs.get("latitude"),
        obs.get("longitude"),
        obs.get("date_utc"),
        obs.get("parameter"),
        obs.get("aqi"),
        obs.get("value"),
        obs.get("unit"),
        str(obs.get("raw", {}))
    ))
    conn.commit()
    conn.close()

def list_unflagged(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM observations WHERE flagged = 0 LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def flag_and_save_summary(obs_ids: List[str], summary: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE observations SET summary = ?, flagged = 1 WHERE id IN ({})".format(",".join("?"*len(obs_ids))), tuple([summary] + obs_ids))
    conn.commit()
    conn.close()