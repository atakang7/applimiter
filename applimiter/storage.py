import os
import sqlite3
from datetime import date
from enum import IntEnum
from typing import List, Optional, Tuple


class WarnKind(IntEnum):
    """Sentinel minute_mark values for non-threshold warned/blocked events.

    Real warn_at_minutes marks are always >= 0, so negative values are safe
    to reuse as distinct "event happened today" flags in the same table.
    """

    LIMIT_HIT = -1
    TIME_LOCKED = -2


class Storage:
    def __init__(self, state_dir: str) -> None:
        os.makedirs(state_dir, exist_ok=True)
        self.db_path = os.path.join(state_dir, "usage.db")
        self.conn = sqlite3.connect(self.db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS usage (
                date TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                category TEXT NOT NULL,
                seconds INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (date, rule_name)
            );
            CREATE TABLE IF NOT EXISTS warned (
                date TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                minute_mark INTEGER NOT NULL,
                PRIMARY KEY (date, rule_name, minute_mark)
            );
            CREATE TABLE IF NOT EXISTS nudged (
                date TEXT NOT NULL,
                minute_mark INTEGER NOT NULL,
                PRIMARY KEY (date, minute_mark)
            );
            """
        )
        self.conn.commit()

    @staticmethod
    def today() -> str:
        return date.today().isoformat()

    def add_seconds(self, rule_name: str, category: str, seconds: int) -> None:
        d = self.today()

        self.conn.execute(
            """
            INSERT INTO usage (date, rule_name, category, seconds)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date, rule_name) DO UPDATE SET seconds = seconds + excluded.seconds,\n                category = excluded.category
            """,
            (d, rule_name, category, seconds),
        )
        self.conn.commit()

    def get_seconds(self, rule_name: str, d: Optional[str] = None) -> int:
        d = d or self.today()

        row = self.conn.execute(
            "SELECT seconds FROM usage WHERE date = ? AND rule_name = ?", (d, rule_name)
        ).fetchone()

        return row[0] if row else 0

    def get_all_usage(self, d: Optional[str] = None) -> List[Tuple[str, str, int]]:
        d = d or self.today()

        rows = self.conn.execute(
            "SELECT rule_name, category, seconds FROM usage WHERE date = ? ORDER BY seconds DESC", (d,)
        ).fetchall()

        return rows

    def has_warned(self, rule_name: str, minute_mark: int, d: Optional[str] = None) -> bool:
        d = d or self.today()

        row = self.conn.execute(
            "SELECT 1 FROM warned WHERE date = ? AND rule_name = ? AND minute_mark = ?",
            (d, rule_name, minute_mark),
        ).fetchone()

        return row is not None

    def mark_warned(self, rule_name: str, minute_mark: int, d: Optional[str] = None) -> None:
        d = d or self.today()

        self.conn.execute(
            "INSERT OR IGNORE INTO warned (date, rule_name, minute_mark) VALUES (?, ?, ?)",
            (d, rule_name, minute_mark),
        )
        self.conn.commit()

    def has_nudged(self, minute_mark: int, d: Optional[str] = None) -> bool:
        d = d or self.today()

        row = self.conn.execute(
            "SELECT 1 FROM nudged WHERE date = ? AND minute_mark = ?", (d, minute_mark)
        ).fetchone()

        return row is not None

    def mark_nudged(self, minute_mark: int, d: Optional[str] = None) -> None:
        d = d or self.today()

        self.conn.execute(
            "INSERT OR IGNORE INTO nudged (date, minute_mark) VALUES (?, ?)", (d, minute_mark)
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
