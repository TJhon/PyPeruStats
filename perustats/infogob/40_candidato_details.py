import json
import sqlite3

import pandas as pd
import requests

# import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://infogob.jne.gob.pe"


def get_control_text(soup, label_text):
    label = soup.find("span", class_="etiqueta", string=label_text)
    if label:
        control = label.find_next_sibling("span", class_="control")
        return control.get_text(strip=True) if control else None
    return None


def get_info_politico(url):
    url_politico = BASE_URL + url

    basic_info_soup = requests.get(url_politico, timeout=2)
    soup = BeautifulSoup(basic_info_soup.content, "html.parser")
    # token = soup.select_one("#key").get("value")
    # _, id_pol = url.split('partidario_')
    datos = {"url_candidato": url}
    datos["fecha_nacimiento"] = get_control_text(soup, "Fecha de nacimiento")
    datos["region"] = get_control_text(soup, "Región")
    datos["provincia"] = get_control_text(soup, "Provincia")
    datos["distrito"] = get_control_text(soup, "Distrito")
    id_persona = soup.find("input", id="IdPersona")
    datos["id_persona"] = id_persona["value"] if id_persona else None
    hv_items = soup.select(".lista-hojavida li a")
    datos["num_hojas_vida"] = len(hv_items)

    pg_items = soup.select(".lista-plangobierno li a")
    datos["num_planes_gobierno"] = len(pg_items)

    return datos, hv_items, pg_items


def details_hoja_vida(hojas_vida: list, data):
    def clean_hoja_vida(hoja_vida):
        data_codigo_raw = hoja_vida.get("data-codigo")
        json_data_raw = {}
        if data_codigo_raw:
            json_data_raw = json.loads(data_codigo_raw)
        hoja_vida_clean = {
            "url_candidato": data.get("url_candidato"),
            "data_metodo": hoja_vida.get("data-metodo"),
            "data_tipo_link": hoja_vida.get("data-tipolink"),
            "data_url": hoja_vida.get("data-url"),
            "name_file": hoja_vida.get_text(strip=True),
            "href": hoja_vida.get("href"),
            "metodo_http": json_data_raw.get("TxMetodoHttp"),
            "id_hoja_vida": json_data_raw.get("IdHojaVida"),
            "id_org_politica": json_data_raw.get("IdOrgPolitica"),
            "id_proceso": json_data_raw.get("IdOrgPolitica"),
            "txt_org_politica": json_data_raw.get("TxOrgPolitica"),
        }
        return hoja_vida_clean

    hvs = [clean_hoja_vida(hv) for hv in hojas_vida]
    return pd.DataFrame(hvs)


def details_plan_gob(planes, data):

    planes_clean = [
        {
            "url_candidato": data.get("url_candidato"),
            "nombre": a.get_text(strip=True),
            "href": a.get("href"),
            "data_url": a.get("data-url"),
            "data_tipolink": a.get("data-tipolink"),
            "data_metodo": a.get("data-metodo"),
        }
        for a in planes
    ]
    return pd.DataFrame(planes_clean)


conn = sqlite3.connect("./data/infogob/db.db")

url_politico = pd.read_sql(
    """
    SELECT DISTINCT url_politico
    FROM eleccion_candidatos
    """,
    con=conn,
)

procesados_org = pd.read_sql(
    """
    SELECT DISTINCT url_candidato as url_politico
    FROM candidato_planes_gob
    """,
    con=conn,
)


pendientes = (
    url_politico.merge(
        procesados_org["url_politico"], on="url_politico", how="left", indicator=True
    )
    .query('_merge == "left_only"')
    .drop(columns="_merge")
)


for url_pol in tqdm(pendientes["url_politico"].values, desc="detalle de politicos"):
    try:
        info_candidato, info_hojas_vida, info_planes = get_info_politico(url_pol)

        df_candidato = pd.DataFrame([info_candidato])
        df_hv = pd.DataFrame(details_hoja_vida(info_hojas_vida, info_candidato))
        df_pl = pd.DataFrame(details_plan_gob(info_planes, info_candidato))

        df_candidato.to_sql("candidato_info", con=conn, if_exists="append")
        df_hv.to_sql("candidatos_hoja_vida", con=conn, if_exists="append")
        df_pl.to_sql("candidato_planes_gob", con=conn, if_exists="append")
    except:
        pass
