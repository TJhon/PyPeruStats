"""
utilities para hacer las peticiones al backend
"""

from dataclasses import dataclass

import pandas as pd
import requests
from bs4 import BeautifulSoup

from perustats.MEF.utils.html import STATESHTML, extract_states, get_button_label
from perustats.MEF.utils.tables import html_table_to_dataframe


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
        "__VIEWSTATE": state._view_state,
        "__EVENTVALIDATION": state._event_validation,
        "ctl00$CPH1$DrpYear": str(year),
        "ctl00$CPH1$TxtSearch": search_query,
        "__ASYNCPOST": True,
    }

    # Solo agregar DrpActProy para gastos
    if tipo == "gasto":
        payload["ctl00$CPH1$DrpActProy"] = act_proy

    return payload


def build_payload(
    soup,
    year: int,
    state: STATESHTML,
    button_key: str,
    grp: str,
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
    base_payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": state._view_state,
        "__EVENTVALIDATION": state._event_validation,
        **extras,
        "ctl00$CPH1$DrpYear": year,
        button_key: get_button_label(soup, button_key),
        "grp1": grp,
    }

    # Solo agregar DrpActProy para gastos
    if tipo == "gasto":
        base_payload["ctl00$CPH1$DrpActProy"] = act_proy

    return base_payload


@dataclass
class PostInfo:
    states: STATESHTML
    df: pd.DataFrame
    soup: BeautifulSoup


def post_info(
    session: requests.Session, url: str, payload: dict, columns: list
) -> PostInfo:
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
    return PostInfo(states=states, df=df, soup=soup)


@dataclass
class MefSession:
    session: requests.Session
    states: STATESHTML
    df: pd.DataFrame
    soup: BeautifulSoup


def init_session(url: str, columns: list, convert: bool) -> MefSession:
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
    df = html_table_to_dataframe(soup, columns=columns, convert=convert)

    initial_states = extract_states(soup)

    initial_session = MefSession(
        session=session, states=initial_states, df=df, soup=soup
    )

    return initial_session
