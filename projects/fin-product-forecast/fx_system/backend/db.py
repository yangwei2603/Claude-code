from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).resolve().parents[1] / "fx_data.sqlite3"


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS fx_rates (
              source TEXT NOT NULL,
              pair TEXT NOT NULL,
              ts TEXT NOT NULL,
              rate REAL NOT NULL,
              PRIMARY KEY (source, pair, ts)
            );

            CREATE TABLE IF NOT EXISTS model_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              pair TEXT NOT NULL,
              trained_at TEXT NOT NULL,
              horizon INTEGER NOT NULL,
              slope REAL NOT NULL,
              intercept REAL NOT NULL,
              inertia REAL NOT NULL,
              regimes_json TEXT NOT NULL
            );
            """
        )


def upsert_rates(rows: Iterable[tuple[str, str, str, float]]) -> int:
    inserted = 0
    with conn() as c:
        for source, pair, ts, rate in rows:
            cur = c.execute(
                """
                INSERT OR IGNORE INTO fx_rates(source, pair, ts, rate)
                VALUES (?, ?, ?, ?)
                """,
                (source, pair, ts, rate),
            )
            inserted += cur.rowcount
    return inserted


def get_rates(pair: str, limit: int = 500) -> list[sqlite3.Row]:
    with conn() as c:
        return c.execute(
            """
            SELECT source, pair, ts, rate
            FROM fx_rates
            WHERE pair=?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (pair.upper(), limit),
        ).fetchall()


def save_model_run(
    pair: str,
    trained_at: str,
    horizon: int,
    slope: float,
    intercept: float,
    inertia: float,
    regimes_json: str,
) -> int:
    with conn() as c:
        cur = c.execute(
            """
            INSERT INTO model_runs(pair, trained_at, horizon, slope, intercept, inertia, regimes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (pair.upper(), trained_at, horizon, slope, intercept, inertia, regimes_json),
        )
        return int(cur.lastrowid)


def latest_model(pair: str):
    with conn() as c:
        return c.execute(
            """
            SELECT * FROM model_runs
            WHERE pair=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (pair.upper(),),
        ).fetchone()
