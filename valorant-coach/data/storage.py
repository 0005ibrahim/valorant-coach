"""
SQLite persistence. Two tables: matches (summary) and rounds (economy detail).
Kept simple on purpose — this is not meant to scale past one player's history
on a local machine. Swap for Postgres later if you ever need multi-user.
"""
import sqlite3
from contextlib import contextmanager
from config import DB_PATH
from data.models import MatchSummary, RoundEconomy, BuyType

SCHEMA = """
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    map_name TEXT,
    puuid TEXT,
    agent TEXT,
    final_score_won INTEGER,
    final_score_lost INTEGER,
    match_won INTEGER,
    pulled_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rounds (
    match_id TEXT,
    round_number INTEGER,
    puuid TEXT,
    loadout_value INTEGER,
    spent_credits INTEGER,
    remaining_credits INTEGER,
    buy_type TEXT,
    round_won INTEGER,
    kills INTEGER,
    deaths INTEGER,
    plant_or_defuse INTEGER,
    PRIMARY KEY (match_id, round_number, puuid)
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def save_match(summary: MatchSummary):
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO matches
               (match_id, map_name, puuid, agent, final_score_won, final_score_lost, match_won)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (summary.match_id, summary.map_name, summary.puuid, summary.agent,
             summary.final_score_won, summary.final_score_lost, int(summary.match_won)),
        )
        for r in summary.rounds:
            conn.execute(
                """INSERT OR REPLACE INTO rounds
                   (match_id, round_number, puuid, loadout_value, spent_credits,
                    remaining_credits, buy_type, round_won, kills, deaths, plant_or_defuse)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.match_id, r.round_number, r.puuid, r.loadout_value, r.spent_credits,
                 r.remaining_credits, r.buy_type.value, int(r.round_won), r.kills, r.deaths,
                 int(r.plant_or_defuse)),
            )


def get_rounds_for_puuid(puuid: str) -> list[RoundEconomy]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM rounds WHERE puuid = ? ORDER BY match_id, round_number", (puuid,)
        ).fetchall()

    return [
        RoundEconomy(
            match_id=row["match_id"],
            round_number=row["round_number"],
            puuid=row["puuid"],
            loadout_value=row["loadout_value"],
            spent_credits=row["spent_credits"],
            remaining_credits=row["remaining_credits"],
            buy_type=BuyType(row["buy_type"]),
            round_won=bool(row["round_won"]),
            kills=row["kills"],
            deaths=row["deaths"],
            plant_or_defuse=bool(row["plant_or_defuse"]),
        )
        for row in rows
    ]


def get_matches_for_puuid(puuid: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM matches WHERE puuid = ? ORDER BY pulled_at DESC", (puuid,)
        ).fetchall()
    return [dict(row) for row in rows]
