from datetime import datetime
from pathlib import Path

BASE_URL = "https://estadisticas.bcrp.gob.pe/"
CLASS_DIV_DROPDOWN = "tcg-elevator"

SERIES_URL = BASE_URL + "/estadisticas/series/{type}"

FREQ = ["diarias", "mensuales", "trimestrales", "anuales"]

FREQ_MAP = {"diarias": "D", "mensuales": "M", "trimestrales": "Q", "anuales": "A"}
GROUP_SIZE = 120


DATE_RANGES = ("1990-01-02", datetime.now().strftime("%Y-%m-%d"))

DB_CACHE = Path("./.cache/bcrp")
DB_PATH = DB_CACHE / "bcrp.db"
RELEASES = DB_CACHE / "releases" / "grupos"
SERIES_TABLE = "metadata_series_bcrp"
