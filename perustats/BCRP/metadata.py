"""
metadata.py
-----------
Scrapes the full BCRP series catalogue and exposes a validator that checks
user-supplied codes against the downloaded metadata.

Responsibilities
~~~~~~~~~~~~~~~~
* Download series tables from the BCRP statistics website for all four
  frequencies (daily, monthly, quarterly, annual).
* Persist the catalogue to SQLite so subsequent runs skip the scrape.
* Expose :func:`validate_codes` to warn about unknown / inactive codes before
  any API request is made.

The metadata table is fetched **once** at import/instantiation time; it is
never refreshed automatically. Call :func:`refresh_metadata` explicitly to
force a re-scrape (e.g. to pick up newly published series).
"""

import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from rich import print
from tqdm import tqdm

from .models import (
    CACHE_DB,
    CLASS_DIV_DROPDOWN,
    FREQ_WEB_LABELS,
    FREQ_WEB_MAP,
    METADATA_TABLE,
    SERIES_WEB_URL,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def _clean_text(text: str) -> str:
    """Collapse whitespace and strip leading/trailing spaces."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*-\s*\(\d+ series\).*$", "", text).strip()
    return text


def _parse_series_table(table) -> pd.DataFrame:
    """
    Extract code + description rows from a BeautifulSoup ``<table>`` element.

    Returns an empty DataFrame if the table is ``None`` or has no parseable
    rows.
    """
    rows = []
    for tr in table.find_all("tr")[1:]:  # saltar el header
        tds = tr.find_all("td")
        if not tds:
            continue

        # Extraer código y link
        codigo_td = tds[1].find("a")
        serie_td = tds[2].find("a")

        rows.append(
            {
                "code": _clean_text(codigo_td.text) if codigo_td else None,
                "description": _clean_text(serie_td.text) if serie_td else None,
                "fecha_inicio": _clean_text(tds[3].text),
                "fecha_fin": _clean_text(tds[4].text),
                "url": codigo_td["href"] if codigo_td else None,
                "last_update": _clean_text(tds[5].text),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


def _scrape_metadata() -> pd.DataFrame:
    """
    Download the full BCRP series catalogue from the statistics website.

    Returns
    -------
    pandas.DataFrame
        Columns: ``code``, ``description``, ``group``, ``source``,
        ``freq_label``, ``freq`` (canonical D/M/Q/A indicator).
    """
    all_frames: list[pd.DataFrame] = []

    for freq_label in FREQ_WEB_LABELS:
        url = SERIES_WEB_URL.format(type=freq_label)
        logger.debug("Scraping %s", url)

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        dropdowns = soup.find_all("div", {"class": CLASS_DIV_DROPDOWN})

        for section in tqdm(dropdowns, desc=freq_label, leave=False):
            # --- group name ---
            h2 = section.find("h2")
            group_name = _clean_text(h2.get_text()) if h2 else ""

            # --- source ---
            try:
                fuente = section.find("p", {"class": "fuente"}).get_text()
                fuente = fuente.replace("Fuente: ", "").strip()
            except AttributeError:
                fuente = None

            # --- series table ---
            table = section.find("table", {"class": "series"})
            df = _parse_series_table(table)
            if df.empty:
                continue

            df["group"] = group_name
            df["source"] = fuente
            df["freq_label"] = freq_label
            df["freq"] = FREQ_WEB_MAP[freq_label]
            all_frames.append(df)

    if not all_frames:
        logger.warning("No metadata was scraped — check network connectivity.")
        return pd.DataFrame()

    metadata = pd.concat(all_frames, ignore_index=True)

    return metadata


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _save_metadata(df: pd.DataFrame, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        df.to_sql(METADATA_TABLE, conn, if_exists="replace", index=False)
    logger.info("Metadata saved to %s (%d rows).", db_path, len(df))


def _load_metadata(db_path: Path) -> Optional[pd.DataFrame]:
    if not os.path.exists(db_path):
        return None
    try:
        with sqlite3.connect(db_path) as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            if METADATA_TABLE not in tables:
                return None
            df = pd.read_sql(f"SELECT * FROM {METADATA_TABLE}", conn)
            if df.empty:
                return None
            return df
    except Exception as exc:
        logger.warning("Could not load metadata from cache: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


class BCRPMetadata:
    """
    Manages the BCRP series catalogue used for code validation.

    The catalogue is loaded from SQLite on first instantiation. If no cached
    copy exists the website is scraped automatically (~10 s) and the result
    is persisted for future runs.

    Parameters
    ----------
    db_path:
        Full path to the SQLite file (shared with the data cache).

    Usage
    -----
    >>> meta = BCRPMetadata("cache/bcrp_cache.db")
    >>> valid, invalid = meta.validate_codes(["RD16085DA", "FAKE_CODE"])
    >>> # UserWarning: codes not found in metadata: ['FAKE_CODE']

    >>> meta.refresh()          # force a full re-scrape
    >>> meta.search("inflacion") # returns matching rows (future use)
    """

    def __init__(self, db_path: str = CACHE_DB) -> None:

        self._db_path = Path(db_path)
        self._df: Optional[pd.DataFrame] = None
        self._ensure_loaded()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Load from SQLite; scrape from web if no cache exists yet."""
        df = _load_metadata(self._db_path)
        if df is not None:
            self._df = df
            logger.info("Metadata loaded from cache (%d series).", len(df))
        else:
            logger.info("No cached metadata found — scraping BCRP website…")
            self.refresh()

    def refresh(self) -> None:
        """
        Force a full re-scrape of the BCRP catalogue and overwrite the cache.

        Call this whenever you suspect the catalogue has been updated (e.g.
        new series published by the BCRP).
        """
        df = _scrape_metadata()
        if not df.empty:
            _save_metadata(df, self._db_path)
            self._df = df
            logger.info("Metadata refreshed (%d series).", len(df))
        else:
            logger.error("Metadata refresh failed — catalogue is empty.")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_codes(self, codes: list[str]) -> tuple[list[str], list[str]]:
        """
        Check *codes* against the downloaded catalogue.

        Parameters
        ----------
        codes:
            Series codes supplied by the user.

        Returns
        -------
        valid_codes:
            Codes found in the catalogue.
        invalid_codes:
            Codes **not** found. A :class:`UserWarning` is also emitted so
            the issue is visible even when the caller ignores the return value.

        Examples
        --------
        >>> valid, invalid = meta.validate_codes(["RD16085DA", "MADE_UP"])
        UserWarning: The following codes were not found in the BCRP catalogue
        and will be skipped: ['MADE_UP']
        """
        if self._df is None or self._df.empty:
            logger.warning(
                "Metadata catalogue is unavailable — skipping code validation."
            )
            return list(codes), []

        known = set(self._df["code"].str.upper())
        valid, invalid = [], []

        for code in codes:
            (valid if code.strip().upper() in known else invalid).append(
                code.upper().strip()
            )

        _df_codes = self._df.query("code in @valid")
        # print({"valids": valid})
        names_codes = {}
        for i, row in _df_codes.iterrows():
            name = row.get("group") + " - " + row.get("description")
            names_codes[name] = row["code"].lower()

        if invalid:
            import warnings

            warnings.warn(
                f"The following codes were not found in the BCRP catalogue "
                f"and will be skipped: {invalid}",
                UserWarning,
                stacklevel=3,
            )

        return valid, names_codes, _df_codes, invalid

    # ------------------------------------------------------------------
    # Introspection helpers (ready for future search integration)
    # ------------------------------------------------------------------

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """Full metadata catalogue as a DataFrame."""
        return self._df

    def search(self, query: str) -> pd.DataFrame:
        """
        Return catalogue rows whose description contains *query* (case-insensitive).

        This is a simple substring search intentionally left minimal so that a
        semantic/embedding-based search layer can be plugged in later without
        changing the interface.

        Parameters
        ----------
        query:
            Free-text search term, e.g. ``'inflacion'``, ``'tipo de cambio'``.

        Returns
        -------
        pandas.DataFrame
            Matching rows with columns ``code``, ``description``, ``group``,
            ``source``, ``freq_label``.
        """
        if self._df is None or self._df.empty:
            return pd.DataFrame()

        mask = self._df["description"].str.contains(query, case=False, na=False)
        return self._df[mask].reset_index(drop=True)

    def codes_for_frequency(self, frequency: str) -> list[str]:
        """
        Return all known codes for a given frequency.

        Parameters
        ----------
        frequency:
            Canonical indicator (``'D'``, ``'M'``, ``'Q'``, ``'A'``) or any
            accepted alias (``'daily'``, ``'monthly'``, etc.).
        """
        from .models import resolve_frequency

        freq = resolve_frequency(frequency)
        if self._df is None:
            return []
        return self._df[self._df["freq"] == freq]["code"].tolist()


if __name__ == "__main__":
    meta = BCRPMetadata()
    # meta.refresh()
    valid, invalid = meta.validate_codes(["RD16085DA", "FAKE_CODE", "PM06178MA"])
    print(valid)
    ss = meta.search("indice")
    print(ss)
