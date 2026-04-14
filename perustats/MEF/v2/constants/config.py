from dataclasses import dataclass
from typing import List, Literal

from .reference import (
    GASTO_URL_V4,
    GASTO_URL_V5,
    GASTO_URL_V6,
    GASTO_URL_V7,
    INGRESO_URL_V4,
    INGRESO_URL_V5,
    INGRESO_URL_V6,
)
from .tables import COLUMNS_GASTO_V4, COLUMNS_GASTO_V5, COLUMNS_INGRESO


@dataclass(frozen=True)
class Config:
    years: range
    url: str
    columns: List[str]


CONFIG_GASTO = {
    "v4": Config(range(2009, 2012), GASTO_URL_V4, COLUMNS_GASTO_V4),
    "v5": Config(range(2012, 2016), GASTO_URL_V5, COLUMNS_GASTO_V5),
    "v6": Config(range(2016, 2024), GASTO_URL_V6, COLUMNS_GASTO_V5),
    "v7": Config(range(2024, 2027), GASTO_URL_V7, COLUMNS_GASTO_V5),
}

CONFIG_INGRESO = {
    "v4": Config(range(2009, 2012), INGRESO_URL_V4, COLUMNS_INGRESO),
    "v5": Config(range(2012, 2016), INGRESO_URL_V5, COLUMNS_INGRESO),
    "v6": Config(range(2016, 2027), INGRESO_URL_V6, COLUMNS_INGRESO),
}


# ============================================
# FUNCIONES DE DETECCIÓN DE VERSIÓN
# ============================================


def get_config(year: int, tipo: Literal["gasto", "ingreso"] = "gasto") -> Config:
    configs = CONFIG_GASTO if tipo == "gasto" else CONFIG_INGRESO

    for version, config in configs.items():
        # print(config)
        if year in config.years:
            return config

    raise ValueError(f"Año {year} no soportado para tipo '{tipo}'")
