from dataclasses import dataclass

from bs4 import BeautifulSoup

print("asv")


@dataclass
class STATESHTML:
    _view_state: str
    _event_validation: str

    def _short(self, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 5:
            return value
        return f"{value[:10]}...{value[-5:]}"

    def __repr__(self) -> str:
        return (
            f"STATESHTML("
            f"view_state='{self._short(self._view_state)}', "
            f"event_validation='{self._short(self._event_validation)}'"
            f")"
        )


def get_button_label(soup: BeautifulSoup, id_button_label: str) -> str:
    label = soup.find("input", {"name": id_button_label})
    button_label = label.get("value")
    if button_label is not None:
        return button_label
    raise ValueError("No existe o no se implemente esa iteraccion con ese boton")


def extract_states(soup: BeautifulSoup) -> STATESHTML:
    """
    Extrae los estados de ViewState y EventValidation del HTML

    Args:
        soup: BeautifulSoup object con el HTML

    Returns:
        Diccionario con __VIEWSTATE y __EVENTVALIDATION
    """
    viewstate = soup.select_one("#__VIEWSTATE")
    eventvalidation = soup.select_one("#__EVENTVALIDATION")
    states = STATESHTML(
        _view_state=viewstate["value"] if viewstate else "",
        _event_validation=eventvalidation["value"] if eventvalidation else "",
    )
    return states


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
