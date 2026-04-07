"""
models.py
---------
Data models, constants, and type definitions for the BCRP data processor.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

CACHE_DB: str = "./data/bcrp_cache.db"

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

BASE_API_URL = (
    "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
    "/{codes}/json/{begin}/{end}/ing"
)

# ---------------------------------------------------------------------------
# Frequency helpers
# ---------------------------------------------------------------------------

VALID_FREQUENCIES = frozenset({"D", "M", "Q", "A"})

# Human-readable aliases → canonical indicator
# Accepted: "daily" | "monthly" | "quarterly" | "yearly" | "d" | "m" | "q" | "a"
FREQ_ALIAS_MAP: dict[str, str] = {
    "daily": "D",
    "monthly": "M",
    "quarterly": "Q",
    "yearly": "A",
    "annual": "A",
    "d": "D",
    "m": "M",
    "q": "Q",
    "a": "A",
}

# strptime/strftime formats used by the BCRP API response dates
REF_DATE_FORMATS: dict[str, str] = {
    "A": "%Y",
    "Q": "Q",  # handled separately via PeriodIndex
    "M": "%b.%Y",
    "D": "%d.%b.%y",
}

# Spanish → English month abbreviations returned by the API
SPANISH_MONTH_MAP: dict[str, str] = {
    "Ene": "Jan",
    "Abr": "Apr",
    "Ago": "Aug",
    "Set": "Sep",
    "Dic": "Dec",
}

DEFAULT_START_DATE = "1990-01-02"

# ---------------------------------------------------------------------------
# Metadata scraping constants
# ---------------------------------------------------------------------------

BASE_WEB_URL = "https://estadisticas.bcrp.gob.pe"
SERIES_WEB_URL = BASE_WEB_URL + "/estadisticas/series/{type}"
CLASS_DIV_DROPDOWN = "tcg-elevator"

FREQ_WEB_LABELS = ["diarias", "mensuales", "trimestrales", "anuales"]

FREQ_WEB_MAP: dict[str, str] = {
    "diarias": "D",
    "mensuales": "M",
    "trimestrales": "Q",
    "anuales": "A",
}


# SQLite table names
METADATA_TABLE = "metadata"  # full catalogue scraped from the BCRP website
SERIES_TABLE = "series"  # active-codes subset used for validation


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


def _format_date_for_frequency(
    date_str: str, frequency: str, fmt: str = "%Y-%m-%d"
) -> str:
    """
    Convert a YYYY-MM-DD date string to the format expected by the BCRP API
    for the given frequency.

    Parameters
    ----------
    date_str:
        Date in ``fmt`` format (default ``%Y-%m-%d``).
    frequency:
        One of ``'D'``, ``'M'``, ``'Q'``, ``'A'``.
    fmt:
        strptime format of *date_str*.

    Returns
    -------
    str
        Date string formatted for the BCRP API endpoint.

    Examples
    --------
    >>> _format_date_for_frequency("2023-06-15", "D")
    '2023-06-15'
    >>> _format_date_for_frequency("2023-06-15", "M")
    '2023-06'
    >>> _format_date_for_frequency("2023-06-15", "Q")
    '2023-2'
    >>> _format_date_for_frequency("2023-06-15", "A")
    '2023'
    """
    dt = datetime.strptime(date_str, fmt)
    if frequency == "D":
        return dt.strftime("%Y-%m-%d")
    if frequency == "M":
        return dt.strftime("%Y-%m")
    if frequency == "Q":
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-{quarter}"
    if frequency == "A":
        return dt.strftime("%Y")
    raise ValueError(f"Unknown frequency: {frequency!r}")


@dataclass
class BCRPSeries:
    """
    A single batched request to the BCRP API.

    Attributes
    ----------
    codes:      Series codes.
    frequency:  Canonical indicator (D / M / Q / A). Aliases are resolved.
    start_date: Start date (YYYY-MM-DD).
    end_date:   End date   (YYYY-MM-DD).
    freq_codes: Codes by frecuencia
    """

    codes: list[str]
    start_date: str
    end_date: str

    def __post_init__(self) -> None:

        freq_codes = defaultdict(list)
        for code in self.codes:
            code = code.upper()
            freq = code[-1]
            if freq in FREQ_WEB_MAP.values():
                freq_codes[freq].append(code)
        self.freq_codes = dict(freq_codes)

        date_limits = dict()

        for freq in self.freq_codes.keys():
            start_n = _format_date_for_frequency(self.start_date, freq)
            end_n = _format_date_for_frequency(self.end_date, freq)
            date_limits[freq] = dict(start_date=start_n, end_date=end_n)

        self.date_limits = date_limits

        if not self.codes:
            raise ValueError("codes list must not be empty.")
