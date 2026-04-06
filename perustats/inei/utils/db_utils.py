"""
Database manager: SQLite-backed cache and progress tracker for module downloads.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

from ..constants import CACHE_MICRODATOS, PROGRESS_COLUMNS


_CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {CACHE_MICRODATOS} (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    survey        TEXT    NOT NULL,
    year          INTEGER NOT NULL,
    periodo       TEXT    NOT NULL,
    number        TEXT,
    year_ref      INTEGER,
    period_ref    TEXT,
    survey_code   TEXT,
    survey_name   TEXT,
    module_code   TEXT,
    module_name   TEXT,
    info_sheet    TEXT,
    spss          TEXT,
    stata         TEXT,
    csv           TEXT,
    dbf           TEXT,
    url           TEXT,
    path_download TEXT,
    path_extract  TEXT,
    path_organized TEXT,
    downloaded    INTEGER DEFAULT 0,
    unzipped      INTEGER DEFAULT 0,
    organized     INTEGER DEFAULT 0,
    removed_zip   INTEGER DEFAULT 0,
    UNIQUE(survey, year, periodo, module_code)
)
"""


class DatabaseManager:
    """
    Thin wrapper around a SQLite connection that handles:

    * Schema initialisation
    * Module-list caching (read-through from INEI portal)
    * Per-row progress updates (downloaded / unzipped / organized / removed_zip)
    """

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._ensure_schema()

    # ------------------------------------------------------------------ #
    # Schema                                                               #
    # ------------------------------------------------------------------ #

    def _ensure_schema(self) -> None:
        self.conn.execute(_CREATE_TABLE)
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Cache helpers                                                        #
    # ------------------------------------------------------------------ #

    def get_cached_modules(
        self, survey: str, year: int, periodo: str
    ) -> Optional[pd.DataFrame]:
        """Return cached module rows or ``None`` when the cache is empty."""
        query = f"""
            SELECT * FROM {CACHE_MICRODATOS}
            WHERE survey = ? AND year = ? AND periodo = ?
        """
        try:
            df = pd.read_sql(query, self.conn, params=(survey, year, periodo))
            return df if not df.empty else None
        except Exception:
            return None

    def insert_modules(self, df: pd.DataFrame) -> None:
        """
        Insert new module rows, ignoring rows that already exist
        (UNIQUE constraint on survey + year + periodo + module_code).
        """
        if df.empty:
            return
        # SQLite does not support INSERT OR IGNORE via pandas directly,
        # so we write row-by-row using executemany.
        cols = [c for c in df.columns if c != "id"]
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        sql = (
            f"INSERT OR IGNORE INTO {CACHE_MICRODATOS} ({col_names}) "
            f"VALUES ({placeholders})"
        )
        rows = [tuple(row[c] for c in cols) for _, row in df.iterrows()]
        self.conn.executemany(sql, rows)
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Progress tracking                                                    #
    # ------------------------------------------------------------------ #

    def mark_downloaded(self, url: str, path_download: str) -> None:
        self.conn.execute(
            f"UPDATE {CACHE_MICRODATOS} SET downloaded=1, path_download=? WHERE url=?",
            (path_download, url),
        )
        self.conn.commit()

    def mark_unzipped(self, url: str, path_extract: str) -> None:
        self.conn.execute(
            f"UPDATE {CACHE_MICRODATOS} SET unzipped=1, path_extract=? WHERE url=?",
            (path_extract, url),
        )
        self.conn.commit()

    def mark_organized(self, url: str, path_organized: str) -> None:
        self.conn.execute(
            f"UPDATE {CACHE_MICRODATOS} SET organized=1, path_organized=? WHERE url=?",
            (path_organized, url),
        )
        self.conn.commit()

    def mark_removed_zip(self, url: str) -> None:
        self.conn.execute(
            f"UPDATE {CACHE_MICRODATOS} SET removed_zip=1 WHERE url=?",
            (url,),
        )
        self.conn.commit()

    def reset_download(self, url: str) -> None:
        """Clear all progress flags for *url* (used when force=True)."""
        self.conn.execute(
            f"""UPDATE {CACHE_MICRODATOS}
                SET downloaded=0, unzipped=0, organized=0, removed_zip=0
                WHERE url=?""",
            (url,),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
