# === CONFIGURACIÓN GLOBAL ===

# SURVEYS
## anuales

SURVERY_Y = dict(
    enaho=dict(name="Condiciones de Vida y Pobreza - ENAHO"),
    enapres=dict(name="Encuesta Nacional de Programas Presupuestales - ENAPRES"),
    endes=dict(name="Encuesta Demográfica y de Salud Familiar - ENDES"),
    renamu=dict(name="Registro Nacional de Municipalidades - RENAMU"),
)

## otros

## todas las encuestas

SURVEYS = dict(anual=SURVERY_Y)

SESSION_COOKIE = "ASPSESSIONIDACGTQQBC=GJEEJPNCPHOBIIDCFFDOKFNM"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0"

BASE_URL = dict(
    consulta="https://proyectos.inei.gob.pe/microdatos",
    descarga="https://proyectos.inei.gob.pe/",
)


# File extensions for data files
RELEVANT_EXTENSIONS = {".csv", ".sav", ".dta", ".dbf"}

# Save files
CACHE_MICRODATOS = "inei_microdatos"

## Track de progreso

COLS_PROGRESS = [
    "url",
    "path_download",
    "path_extract",
    "path_orden",
    "downloaded",
    "unzipped",
    "organized",
    "removed_zip",
]

PERIODOS_NAMES = dict(anual=["anual", "unico"])
