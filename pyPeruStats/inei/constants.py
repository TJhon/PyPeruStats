# === CONFIGURACIÓN GLOBAL ===
SURVEYS_CONFIG = {
    "enaho": {"name": "Condiciones de Vida y Pobreza - ENAHO", "default_quarter": "55"},
    "endes": {
        "name": "Encuesta Demográfica y de Salud Familiar - ENDES",
        "default_quarter": "5",
    },
    "enapres": {
        "name": "Encuesta Nacional de Programas Presupuestales - ENAPRES",
        "default_quarter": "18",
    },
}


SESSION_COOKIE = "ASPSESSIONIDSSXCRQBD=XXXXXX"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0"
BASE_URL = "https://proyectos.inei.gob.pe/iinei/srienaho"

# File extensions for data files
RELEVANT_EXTENSIONS = {".csv", ".sav", ".dta", ".dbf"}
