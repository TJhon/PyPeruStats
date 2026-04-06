# extraera informacion como id_eleccion e id_group_eleccion es importante para las peticiones de resultados
import requests
from bs4 import BeautifulSoup
from rich import print
from tqdm import tqdm

from perustats.infogob.constants import (
    BASE_URL,
    URL_ELECCIONES,
    URL_FICHA_ELECCION,
    URL_LISTAR_ELECCIONES,
    URL_RESULTADOS_ELECCION,
)


def get_token(soup):
    token = soup.select_one("#key").get("value")
    return token


def build_payload(istr=None, token=None):
    return {"istrParameters": istr, "token": token}


class ListarEleciones:
    def __init__(self):
        session = requests.Session()
        soup = BeautifulSoup(session.get(URL_ELECCIONES).content, "html.parser")
        print("Fetch procesos electorales")
        self.session = session
        self.soup = soup
        self.token = get_token(soup)
        self._get_proc_electorales()

    def _get_proc_electorales(self):
        options = self.soup.select_one("#IdTipoProceso").find_all("option")

        procesos_electorales = [
            dict(proceso_electoral=option.get_text(strip=True), id=option.get("value"))
            for option in options[1:]
        ]
        self.procesos_electorales = procesos_electorales

    def _listar_elecciones(self, proc_electoral: dict, token: str):
        elecciones = self.session.post(
            URL_LISTAR_ELECCIONES, data=build_payload(proc_electoral.get("id"), token)
        )
        data = elecciones.json().get("Data")
        data = data[1:]  # opciones relevantes
        data = [
            dict(
                **proc_electoral,
                name_eleccion=eleccion.get("Text").title(),
                id_eleccion=eleccion.get("Value"),
            )
            for eleccion in data
        ]
        return data

    def get_all_elecciones(self):
        procesos_electorales = self.procesos_electorales
        elecciones = []
        for proc in tqdm(
            procesos_electorales, desc="Fetch elecciones de procesos electorales"
        ):
            elecion = self._listar_elecciones(proc_electoral=proc, token=self.token)
            if elecion:
                elecciones.append(elecion)
        elecciones = [d for el in elecciones for d in el]
        result = []
        for el in tqdm(elecciones, desc="Fetch de url de redireccion"):
            url, id_group = self._get_redirected_url(el)
            res = {**el, "url_redirect": url, "id_group_eleccion": id_group}
            result.append(res)
        return result

    def _get_redirected_url(self, election: dict):
        id_eleccion = election.get("id_eleccion")
        r = self.session.post(
            URL_FICHA_ELECCION,
            data={"parameter1": id_eleccion},
            allow_redirects=False,
        )
        redirect_url = r.headers["Location"]
        url_resultados = BASE_URL + redirect_url.replace(
            "_normativa_", "_candidatos-y-resultados_"
        )

        soup_resultados = BeautifulSoup(
            requests.get(url_resultados).content, "html.parser"
        )
        id_group_eleccion = soup_resultados.find(
            "input", {"id": "IdGrupoEleccion"}
        ).get("value")
        # time.sleep(1)

        return url_resultados, id_group_eleccion


istr_ids = [
    {"proceso_electoral": "ELECCIONES PRESIDENCIALES", "istr_value": 1001},
    {"proceso_electoral": "ELECCIONES CONGRESALES", "istr_value": 5111},
    {"proceso_electoral": "ELECCIONES PARLAMENTO ANDINO", "istr_value": 1011},
    {"proceso_electoral": "ELECCIONES REGIONALES", "istr_value": 2001},
    {"proceso_electoral": "ELECCIONES MUNICIPALES PROVINCIALES", "istr_value": 3001},
    {"proceso_electoral": "ELECCIONES MUNICIPALES DISTRITALES", "istr_value": 4001},
    {"proceso_electoral": "ELECCIONES MUNICIPALES COMPLEMENTARIAS", "istr_value": 4001},
    {
        "proceso_electoral": "CONSULTA POPULAR DE REVOCATORIA DEL MANDATO DE AUTORIDADES MUNICIPALES",
        "istr_value": 4001,
    },
    {"proceso_electoral": "REFERENDUM Y OTRAS CONSULTAS", "istr_value": 1001},
    {"proceso_electoral": "NUEVAS ELECCIONES MUNICIPALES", "istr_value": 4001},
]

istr_map = {d["proceso_electoral"]: d["istr_value"] for d in istr_ids}

if __name__ == "__main__":
    info = ListarEleciones().get_all_elecciones()
    from collections import defaultdict

    for item in info:
        item["istr_value"] = istr_map.get(item["proceso_electoral"])

    groups = defaultdict(list)
    for item in info:
        key = (item["proceso_electoral"], item["id"])
        groups[key].append(item)

    session = requests.Session()
    soup = BeautifulSoup(session.get(URL_ELECCIONES).content, "html.parser")
    TOKEN = get_token(soup)

    for eleccion in tqdm(info):
        id_eleccion = eleccion["id_eleccion"]
        id_group_eleccion = eleccion["id_group_eleccion"]
        prev_istr = eleccion["istr_value"]

        istr = f"{prev_istr}{id_eleccion}@{id_group_eleccion}"

        # se obtiene los lugares de resultados
        params = {"istrParameters": istr}
        payload = {"token": TOKEN}
        r = session.post(URL_RESULTADOS_ELECCION, params=params, json=payload)
        soup_n = BeautifulSoup(r.content, "html.parser")
        n_level = len(soup_n.select_one("div#CandidatosResultados").find_all("select"))
        eleccion["n_level"] = n_level

    import pandas as pd

    pd.DataFrame(info).to_csv("0_procesos_electorales.csv", index=False)
