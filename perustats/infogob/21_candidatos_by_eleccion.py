import sqlite3

import pandas as pd
import requests
from bs4 import BeautifulSoup
from rich import print
from tqdm import tqdm

print

URL_CANDIDATOS = "https://infogob.jne.gob.pe/Eleccion/ListarDatosCandidatos"
r = requests.get("https://infogob.jne.gob.pe/", timeout=1)
soup = BeautifulSoup(r.text, "html.parser")
TOKEN = soup.select_one("#key").get("value")


conn = sqlite3.connect("./data/infogob/db.db")


rename_map = {
    "TxOrgPol": "name_org_politica",
    "TxCandidato": "name_candidato",
    "TxRutaPolitico": "url_politico",
    "TxRutaFoto": "url_foto_candidato",
    "TxEstadoCand": "estado_candidatura",
    "TxCargo": "cargo_postula",
    "TxCargoElecto": "cargo_electo",
    "TxRutaSimbolo": "url_simbolo_org_politica",
    "TxRutaOrgPol": "url_org_politica",
    "NuVotosCand": "num_votos_candidato",
}


def post_result(row):
    id_eleccion = row.get("id_eleccion")
    # id_g_eleccion = row.get("id_group_eleccion")
    id_location = row.get("id_location_req")
    id_expediente = row.get("id_expediente")
    istr = f"{id_eleccion}@{id_expediente}@{id_location}"
    payload = {"istrParameters": istr, "token": TOKEN}
    r = requests.post(URL_CANDIDATOS, json=payload, timeout=1)
    r.raise_for_status()
    candidatos = r.json().get("Data", [])
    candidatos = [{**row, **cand} for cand in candidatos]
    df = pd.DataFrame(candidatos)
    df = df.rename(columns=rename_map)
    return df


resultados_org = pd.read_sql(
    """
    SELECT DISTINCT id_eleccion, id_location_req, id_group_eleccion, id_expediente
    FROM resultados_by_org_politica  
    """,
    con=conn,
)

procesados_org = pd.read_sql(
    """
    SELECT DISTINCT id_eleccion, id_location_req, id_group_eleccion, id_expediente
    FROM eleccion_candidatos  
    """,
    con=conn,
)

keys = [
    "id_eleccion",
    "id_location_req",
    "id_group_eleccion",
    "id_expediente",
]

pendientes = (
    resultados_org.merge(procesados_org[keys], on=keys, how="left", indicator=True)
    .query('_merge == "left_only"')
    .drop(columns="_merge")
)


for _, expediente in tqdm(
    pendientes.iterrows(), total=pendientes.shape[0], desc="candidatos"
):
    # print(expediente)
    try:
        df = post_result(expediente)
        df.to_sql("eleccion_candidatos", con=conn, if_exists="append", index=False)
    except:
        pass
