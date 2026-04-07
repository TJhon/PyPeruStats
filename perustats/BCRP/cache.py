"""
cache.py
--------
SQLite cache para series del BCRP.

Estrategia de tablas
~~~~~~~~~~~~~~~~~~~~
* Una tabla por combinación (frecuencia, start_date, end_date):
      series_{FREQ}_{start}_{end}   →  columnas: date + un código por columna
  Si los parámetros cambian → tabla nueva → fetch completo.
  Si los parámetros son iguales pero hay códigos nuevos → solo se piden esos
  y se agregan como columnas nuevas con ALTER TABLE.

* Tabla ``valid_codes_cache`` → acumula metadata de todos los códigos
  válidos que se han descargado (sin duplicados por ``code``).
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers de nombre de tabla
# ---------------------------------------------------------------------------

_VALID_CODES_TABLE = "Codigos Procesados"


def _table_name(freq: str, start_date: str, end_date: str) -> str:
    """Genera un nombre de tabla seguro para SQLite."""
    start = start_date.replace("-", "_").replace("/", "_")
    end = end_date.replace("-", "_").replace("/", "_")
    return f"series_{freq}_{start}_{end}"


# ---------------------------------------------------------------------------
# BCRPCache
# ---------------------------------------------------------------------------


class BCRPCache:
    """
    Interfaz de caché SQLite para series del BCRP.

    Parameters
    ----------
    db_path:
        Ruta al archivo ``.db``. Se crea si no existe.
    """

    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def clean_cache(self):
        """Elimina todas las tablas excepto 'metadata'."""
        with self._connect() as conn:
            cursor = conn.cursor()

            # Obtener todas las tablas excepto 'metadata'
            cursor.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table' AND name != 'metadata';
            """)
            tables = cursor.fetchall()

            # Eliminar cada tabla
            for (table_name,) in tables:
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}";')

            conn.commit()

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _table_exists(self, conn: sqlite3.Connection, table: str) -> bool:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        return cur.fetchone() is not None

    def _columns(self, conn: sqlite3.Connection, table: str) -> set[str]:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return {row[1] for row in cur.fetchall()}

    # ------------------------------------------------------------------
    # Series data
    # ------------------------------------------------------------------

    def cached_codes(self, freq: str, start_date: str, end_date: str) -> set[str]:
        """
        Devuelve los códigos que ya están almacenados en la tabla
        correspondiente a (freq, start_date, end_date).
        Retorna un conjunto vacío si la tabla no existe.
        """
        table = _table_name(freq, start_date, end_date)
        with self._connect() as conn:
            if not self._table_exists(conn, table):
                return set()
            cols = self._columns(conn, table)
            cols.discard("date")
            return {c.upper() for c in cols}

    def load(
        self, freq: str, start_date: str, end_date: str, codes: list[str]
    ) -> Optional[pd.DataFrame]:
        """
        Carga desde caché el DataFrame para los *codes* solicitados.

        Returns ``None`` si la tabla no existe.
        Devuelve solo las columnas disponibles (puede ser subconjunto de *codes*).
        """
        id = ["date"]
        if freq == "Q":
            id = ["date", "yq"]
        table = _table_name(freq, start_date, end_date)
        with self._connect() as conn:
            if not self._table_exists(conn, table):
                return None
            available = self._columns(conn, table) - {"date"}
            wanted = [c for c in codes if c.upper() in {a.upper() for a in available}]
            if not wanted:
                return None
            cols_sql = ", ".join(id + wanted)
            df = pd.read_sql(f"SELECT {cols_sql} FROM {table}", conn)
            return df

    def save(
        self,
        df: pd.DataFrame,
        freq: str,
        start_date: str,
        end_date: str,
    ) -> None:
        """
        Persiste *df* (columnas: ``date`` + códigos) para los parámetros dados.

        - Si la tabla no existe → se crea.
        - Si ya existe y hay columnas nuevas → ALTER TABLE ADD COLUMN.
        - Las filas se insertan con ``INSERT OR REPLACE`` (upsert por ``date``).
        """
        if df is None or df.empty:
            return

        table = _table_name(freq, start_date, end_date)

        with self._connect() as conn:
            if not self._table_exists(conn, table):
                df.to_sql(table, con=conn, index=False, if_exists="replace")
            else:
                # Agregar columnas que falten
                df_last = pd.read_sql(f"select * from {table}", con=conn)
                df_merged = df_last.merge(df, "outer")
                df_merged.to_sql(table, con=conn, index=False, if_exists="replace")

    # ------------------------------------------------------------------
    # valid_codes_cache
    # ------------------------------------------------------------------

    def load_valid_codes(self) -> Optional[pd.DataFrame]:
        """Devuelve el DataFrame acumulado de códigos válidos, o ``None``."""
        with self._connect() as conn:
            if not self._table_exists(conn, _VALID_CODES_TABLE):
                return None
            return pd.read_sql(f"SELECT * FROM {_VALID_CODES_TABLE}", conn)

    def save_valid_codes(self, df: pd.DataFrame) -> None:
        """
        Añade filas nuevas a ``valid_codes_cache`` (sin duplicar por ``code``).
        """
        if df is None or df.empty:
            return

        with self._connect() as conn:
            if not self._table_exists(conn, _VALID_CODES_TABLE):
                df.to_sql(_VALID_CODES_TABLE, conn, if_exists="replace", index=False)
                # Crear índice único en 'code'
                conn.execute(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS "
                    f"idx_{_VALID_CODES_TABLE}_code "
                    f"ON {_VALID_CODES_TABLE}(code)"
                )
            else:
                # INSERT OR IGNORE para no duplicar
                cols = list(df.columns)
                placeholders = ", ".join("?" * len(cols))
                cols_quoted = ", ".join(f'"{c}"' for c in cols)
                conn.executemany(
                    f"INSERT OR IGNORE INTO {_VALID_CODES_TABLE} "
                    f"({cols_quoted}) VALUES ({placeholders})",
                    df.itertuples(index=False, name=None),
                )
            conn.commit()
            logger.info("valid_codes_cache actualizado con %d filas.", len(df))

    # ------------------------------------------------------------------
    # Introspección
    # ------------------------------------------------------------------

    def list_cached_series(self) -> list[dict]:
        """
        Lista todas las tablas de series guardadas con sus metadatos.

        Returns
        -------
        list of dict con claves ``table``, ``freq``, ``start``, ``end``, ``codes``.
        """
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'series_%'"
            )
            tables = [row[0] for row in cur.fetchall()]

        result = []
        for table in tables:
            parts = table.split("_")  # series_{FREQ}_{start}_{end}
            freq = parts[1] if len(parts) > 1 else "?"
            start = parts[2] if len(parts) > 2 else "?"
            end = parts[3] if len(parts) > 3 else "?"
            with self._connect() as conn:
                codes = list(self._columns(conn, table) - {"date"})
            result.append(
                {
                    "table": table,
                    "freq": freq,
                    "start": start,
                    "end": end,
                    "codes": codes,
                }
            )
        return result
