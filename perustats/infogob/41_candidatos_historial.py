import sqlite3

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

conn = sqlite3.connect("./data/infogob/db.db")


BASE_URL = "https://infogob.jne.gob.pe"
HISTORIAL_FICHA_POLITICO = f"{BASE_URL}/Politico/_HistorialFichaPolitico"


r = requests.get(BASE_URL, timeout=1)
soup = BeautifulSoup(r.content, "html.parser")
TOKEN = soup.select_one("#key").get("value")


def parse_content_block(content_div):
    data = {}

    # Organización política
    org_span = content_div.find("span", class_="linkOrgPol")
    if org_span:
        a = org_span.find("a")
        data["organizacion_politica"] = a.get_text(strip=True) if a else None
        data["url_organizacion"] = a["href"] if a and a.has_attr("href") else None
        data["id_organizacion"] = org_span.get("data-val")

    # Etiqueta → control
    for etiqueta in content_div.find_all("span", class_="etiqueta"):
        label = etiqueta.get_text(strip=True).replace(":", "")
        control = etiqueta.find_next_sibling("span", class_="control")
        if not control:
            continue

        value = control.get_text(" ", strip=True)
        key = (
            label.lower()
            .replace(" ", "_")
            .replace("ó", "o")
            .replace("í", "i")
            .replace("é", "e")
            .replace("á", "a")
            .replace("ú", "u")
        )

        data[key] = value

    return data


def join_afiliaciones(html_content, metadata):

    soup = BeautifulSoup(html_content, "html.parser")

    container = soup.find("div", id="HistorialPartidario")

    headers = container.find_all("h5")

    resultado = []

    for h in headers:
        titulo = h.get_text(strip=True).upper()
        # print(titulo)
        content = h.find_next_sibling("div", class_="content")

        if not content:
            continue

        afiliacion = parse_content_block(content)
        afiliacion_meta = {**metadata, **afiliacion}

        if "HISTORIAL DE AFILIACIONES" in titulo:
            afiliacion_meta["activa"] = 0
            resultado.append(afiliacion_meta)
        # if "AFILIACION VIGENTE" in titulo:
        else:
            afiliacion_meta["activa"] = 1
            resultado.append(afiliacion_meta)
        afiliacion_meta = {}

    return resultado


url_politico = pd.read_sql(
    """
    SELECT DISTINCT url_candidato as url_politico, id_persona
    FROM candidato_info
    """,
    con=conn,
)

candidato_hist_partidario = pd.read_sql(
    """
    SELECT DISTINCT url_politico, id_persona
    FROM candidato_hist_partidario
    """,
    con=conn,
)

pendientes = (
    url_politico.merge(
        candidato_hist_partidario["url_politico"],
        on="url_politico",
        how="left",
        indicator=True,
    )
    .query('_merge == "left_only"')
    .drop(columns="_merge")
)


for _, row in tqdm(
    pendientes.iterrows(),
    total=pendientes.shape[0],
    desc="historial politico candidatos",
):
    # row = url_politico.head(2).to_dict("records")[0]
    try:
        id_persona = row.get("id_persona")
        # id_persona = 'ULAs7e4KP8Ec6+/0ElOxMA==Ae'
        url_i = row.get("url_politico")

        r1 = requests.post(
            HISTORIAL_FICHA_POLITICO,
            params={
                "istrParameters": id_persona,
            },
            data={"token": TOKEN},
            timeout=2,
        )
        html_content = r1.content

        ref = join_afiliaciones(html_content, row)
        pd.DataFrame(ref).to_sql(
            "candidato_hist_partidario", con=conn, if_exists="append"
        )
    except:
        pass
