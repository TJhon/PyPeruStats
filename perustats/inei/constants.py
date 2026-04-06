"""
Global configuration constants for the INEI microdata fetcher.
Survey definitions have moved to surveys/registry.py.
"""

BASE_URL = dict(
    consulta="https://proyectos.inei.gob.pe/microdatos",
    descarga="https://proyectos.inei.gob.pe/",
)

SESSION_COOKIE = "ASPSESSIONIDACGTQQBC=GJEEJPNCPHOBIIDCFFDOKFNM"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0"
)

# File extensions treated as data files during organize step
RELEVANT_EXTENSIONS = {".csv", ".sav", ".dta", ".dbf"}

# File extensions treated as documentation
DOC_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".odt"}

# SQLite table name used for caching module lists
CACHE_MICRODATOS = "inei_microdatos"

# Progress-tracking columns stored in the DB alongside each module row
PROGRESS_COLUMNS = [
    "url",
    "path_download",
    "path_extract",
    "path_organized",
    "downloaded",
    "unzipped",
    "organized",
    "removed_zip",
]

# Supported download formats in the order they appear in the INEI table
FORMAT_COLUMNS = ("spss", "stata", "csv", "dbf")
DEFAULT_FORMAT_PREFERENCE = ["stata", "spss", "csv", "dbf"]
