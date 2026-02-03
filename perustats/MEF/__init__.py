"""
MEF Scraper - Sistema unificado de scraping para SIAF MEF

Extrae datos de ingresos y gastos del Sistema Integrado de Administración Financiera
del Ministerio de Economía y Finanzas del Perú.

Uso básico:
    from mef_scraper import MEFScraper

    # Para ingresos
    scraper_ingresos = MEFScraper(tipo='ingreso', master_dir_save='./data/raw/ingresos/')
    scraper_ingresos.run(year=2010, steps=STEPS_INGRESO)

    # Para gastos
    scraper_gastos = MEFScraper(tipo='gasto', master_dir_save='./data/raw/gastos/')
    scraper_gastos.run(year=2010, steps=STEPS_GASTO)
"""

from .constants import detect_version, get_config
from .scraper import MEFScraper
from .utils import (
    extract_states,
    find_row_by_text,
    get_grp_from_row,
    html_table_to_dataframe,
    save_dataframe,
)

__all__ = [
    "MEFScraper",
    "get_config",
    "detect_version",
    "extract_states",
    "html_table_to_dataframe",
    "find_row_by_text",
    "get_grp_from_row",
    "save_dataframe",
]
