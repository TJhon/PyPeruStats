"""
Utilidades compartidas para scraping de SIAF MEF
"""

import re
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup
from rich.console import Console


def get_console():
    return Console(
        force_terminal=not _is_jupyter(), width=100, emoji=False, soft_wrap=True
    )


def _is_jupyter():
    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except Exception:
        return False


console = get_console()


def get_button_label(soup, id_button_label: str) -> str:
    label = soup.find("input", {"name": id_button_label})
    button_label = label.get("value")
    if button_label is not None:
        return button_label
    raise ValueError("No existe o no se implemente esa iteraccion con ese boton")


# ============================================
# EXTRACCIÓN DE ESTADOS Y PARSING HTML
# ============================================


def extract_states(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extrae los estados de ViewState y EventValidation del HTML

    Args:
        soup: BeautifulSoup object con el HTML

    Returns:
        Diccionario con __VIEWSTATE y __EVENTVALIDATION
    """
    viewstate = soup.select_one("#__VIEWSTATE")
    eventvalidation = soup.select_one("#__EVENTVALIDATION")

    return {
        "__VIEWSTATE": viewstate["value"] if viewstate else "",
        "__EVENTVALIDATION": eventvalidation["value"] if eventvalidation else "",
    }


def html_table_to_dataframe(
    soup: BeautifulSoup, columns: list, buscar: str = None, convert: bool = True
) -> pd.DataFrame:
    """
    Convierte la tabla HTML 'Data' en un DataFrame de pandas

    Args:
        soup: BeautifulSoup object con el HTML
        columns: Lista de nombres de columnas
        buscar: Texto a buscar en la columna 'concepto_region' (opcional)
        convert: Si True, convierte números a float

    Returns:
        DataFrame con los datos de la tabla
    """
    table = soup.find("table", class_="Data")

    if table is None:
        raise ValueError("No se encontró la tabla 'Data' en el HTML")

    rows = []

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")

        if not tds:
            continue

        row = []

        for i, td in enumerate(tds):
            text = td.get_text(strip=True)

            # En la primera columna, extraer el valor del input (código grp)
            if i == 0:
                input_tag = td.find("input")
                if input_tag:
                    text = input_tag.get("value", text)

            # Limpiar y convertir números (formato: 3,400,841.50 → 3400841.50)
            if convert and re.match(r"^[\d,]+\.?\d*$", text):
                text = text.replace(",", "")
                try:
                    text = float(text)
                except ValueError:
                    pass

            row.append(text)

        rows.append(row)

    df = pd.DataFrame(rows, columns=columns)

    # Filtrar si se especifica búsqueda
    if buscar is not None:
        df = df[df["concepto_region"].str.contains(buscar, case=False, na=False)]

    return df


# ============================================
# MANIPULACIÓN DE DATAFRAMES
# ============================================


def get_grp_from_row(df: pd.DataFrame, row_index: int = 0) -> str:
    """
    Extrae el código grp de una fila específica del DataFrame

    Args:
        df: DataFrame con los datos
        row_index: Índice de la fila (por defecto 0)

    Returns:
        Código grp como string
    """
    if len(df) == 0:
        raise ValueError("DataFrame vacío")

    if row_index >= len(df):
        raise ValueError(
            f"Índice {row_index} fuera de rango. DataFrame tiene {len(df)} filas"
        )

    return df.iloc[row_index]["codigo_grp"]


def find_row_by_text(df: pd.DataFrame, search_text: str) -> int:
    """
    Encuentra el índice de la primera fila que contiene el texto buscado

    Args:
        df: DataFrame con los datos
        search_text: Texto a buscar en la columna 'concepto_region'

    Returns:
        Índice de la fila encontrada

    Raises:
        ValueError: Si no se encuentra el texto
    """
    mask = df["concepto_region"].str.contains(search_text, case=False, na=False)

    if not mask.any():
        raise ValueError(f"No se encontró ninguna fila con el texto: '{search_text}'")

    return mask.idxmax()


# ============================================
# MANEJO DE ARCHIVOS
# ============================================


def sanitize_filename(text: str) -> str:
    """
    Limpia texto para usar en nombre de archivo

    Args:
        text: Texto a limpiar

    Returns:
        Texto sanitizado
    """
    return "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_" for c in text
    ).strip()


def filename_save(name: str, value: str, save_dir: Path) -> Path:
    """
    Genera la ruta completa para guardar un archivo

    Args:
        name: Nombre del grupo/categoría
        value: Valor específico
        save_dir: Directorio base

    Returns:
        Path completo del archivo
    """
    filename = f"{name}_{sanitize_filename(value)}_loop.csv"
    filepath = save_dir / filename
    return filepath


def save_dataframe(df: pd.DataFrame, save_dir: Path, name: str, value: str) -> Path:
    """
    Guarda un dataframe en la ubicación especificada

    Args:
        df: DataFrame a guardar
        save_dir: Directorio base
        name: Nombre del grupo/categoría
        value: Valor específico

    Returns:
        Path del archivo guardado
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    filepath = filename_save(name, value, save_dir)
    df.to_csv(filepath, index=False)
    return filepath


# ============================================
# COMUNICACIÓN HTTP
# ============================================


def build_search_payload(
    soup: BeautifulSoup,
    year: int,
    state: dict,
    search_query: str,
    search_type: str = "code",
    tipo: str = "gasto",
    act_proy: str = "ActProy",
) -> dict:
    """
    Construye el payload para una búsqueda (por código o descripción)

    Args:
        soup: BeautifulSoup del HTML actual
        year: Año
        state: Estados (ViewState, EventValidation)
        search_query: Texto a buscar
        search_type: "code" para búsqueda por código, "description" para descripción
        tipo: "gasto" o "ingreso"
        act_proy: Solo para gastos

    Returns:
        Diccionario con el payload para POST
    """
    # Determinar qué botón usar
    if search_type == "code":
        event_target = "ctl00$CPH1$BtnSearchByCode"
    elif search_type == "description":
        event_target = "ctl00$CPH1$BtnSearchByDescription"
    else:
        raise ValueError(
            f"search_type debe ser 'code' o 'description', recibido: {search_type}"
        )

    # Construir payload base
    payload = {
        "ctl00$CPH1$ScriptManager1": "ctl00$CPH1$UpdatePanel1|" + event_target,
        "__LASTFOCUS": "",
        "__EVENTTARGET": event_target,
        "__EVENTARGUMENT": "",
        **state,
        "ctl00$CPH1$DrpYear": str(year),
        "ctl00$CPH1$TxtSearch": search_query,
        "__ASYNCPOST": True,
    }

    # Solo agregar DrpActProy para gastos
    if tipo == "gasto":
        payload["ctl00$CPH1$DrpActProy"] = act_proy

    return payload


def has_search_panel(soup: BeautifulSoup) -> bool:
    """
    Verifica si el HTML tiene el panel de búsqueda

    Busca el div con id="ctl00_CPH1_PnlSearch" que contiene:
    - Input de búsqueda: ctl00_CPH1_TxtSearch
    - Botón buscar por código: ctl00_CPH1_BtnSearchByCode
    - Botón buscar por descripción: ctl00_CPH1_BtnSearchByDescription

    Args:
        soup: BeautifulSoup del HTML

    Returns:
        True si existe el panel de búsqueda, False si no
    """
    search_panel = soup.find("div", {"id": "ctl00_CPH1_PnlSearch"})

    if not search_panel:
        return False

    # Verificar que existan los elementos de búsqueda
    search_input = soup.find("input", {"id": "ctl00_CPH1_TxtSearch"})
    btn_code = soup.find("a", {"id": "ctl00_CPH1_BtnSearchByCode"})
    btn_desc = soup.find("a", {"id": "ctl00_CPH1_BtnSearchByDescription"})

    return all([search_input, btn_code, btn_desc])


def build_payload(
    soup,
    year: int,
    state: dict,
    button_key: str,
    grp: str,
    buttons: dict,
    button_labels: dict,
    extras: dict = None,
    tipo: str = "gasto",
    act_proy: str = "ActProy",
) -> dict:
    """
    Construye el payload para el POST

    Args:
        year: Año
        state: Estado (ViewState, EventValidation)
        button_key: Clave del botón a presionar
        grp: Código del grupo
        buttons: Diccionario de botones
        button_labels: Diccionario de labels
        extras: Parámetros adicionales (opcional)
        tipo: "gasto" o "ingreso"

    Returns:
        Diccionario con el payload completo
    """
    if extras is None:
        extras = {}
    id_button = buttons[button_key]
    base_payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        **state,
        **extras,
        "ctl00$CPH1$DrpYear": year,
        # buttons[button_key]: button_labels[button_key],
        id_button: get_button_label(soup, id_button),
        "grp1": grp,
    }

    # Solo agregar DrpActProy para gastos
    if tipo == "gasto":
        base_payload["ctl00$CPH1$DrpActProy"] = act_proy

    return base_payload


def post_info(
    session: requests.Session, url: str, payload: dict, columns: list, updated=False
) -> Tuple[dict, pd.DataFrame]:
    """
    Hace POST y retorna estados y dataframe

    Args:
        session: Sesión de requests
        url: URL del endpoint
        payload: Datos del POST
        columns: Columnas esperadas en la tabla

    Returns:
        Tupla con (estados, dataframe)
    """
    response = session.post(url, data=payload, timeout=30)
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    states = extract_states(soup)
    df = html_table_to_dataframe(soup, columns=columns)
    return states, df, soup


def init_session(url: str) -> Tuple[requests.Session, dict, pd.DataFrame]:
    """
    Inicializa la sesión HTTP y obtiene el estado inicial

    Args:
        url: URL del endpoint

    Returns:
        Tupla con (session, estados_iniciales, dataframe_inicial)
    """
    session = requests.Session()
    response = session.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    initial_states = extract_states(soup)

    return session, initial_states, soup
