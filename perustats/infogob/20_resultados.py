import sqlite3

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from rich import print

from perustats.infogob.constants import URL_LISTAR_RESULTADOS
from perustats.infogob.utils import procesar_respuesta

print
# with httpx.Client(timeout=5.0) as client:
with httpx.Client(timeout=1) as client:
    r = client.get("https://infogob.jne.gob.pe/")
    soup = BeautifulSoup(r.text, "html.parser")
    TOKEN = soup.select_one("#key").get("value")


def post_result(row, client: httpx.Client):
    id_eleccion = row.get("id_eleccion")
    id_g_eleccion = row.get("id_group_eleccion")
    id_location = row.get("id_location_req")
    istr = f"{id_eleccion}@{id_location}@{id_g_eleccion}"
    payload = {"istrParameters": istr, "token": TOKEN}
    r = client.post(URL_LISTAR_RESULTADOS, json=payload)

    r.raise_for_status()
    return r.json()


conn = sqlite3.connect("./data/infogob/db.db")

procesos_electorales = pd.read_sql(
    """
    SELECT id_eleccion, id_group_eleccion,
        id_location_req 
    FROM 
        procesos_electorales_locations
    WHERE procesado = 0 
    """,
    con=conn,
)


def create_tables():
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS resultados_generales (
        id_eleccion TEXT,
        id_location_req TEXT,
        id_group_eleccion TEXT,
        num_votos_emitidos INTEGER,
        num_electores INTEGER,
        num_percent_part REAL,
        num_percent_ausen REAL,
        txt_pregunta TEXT,
        PRIMARY KEY (id_eleccion, id_location_req, id_group_eleccion)
    );

    CREATE TABLE IF NOT EXISTS resultados_by_org_politica (
        id_eleccion TEXT,
        id_location_req TEXT,
        id_group_eleccion TEXT,

        id_expediente TEXT,
        id_localidad TEXT,
        id_org_politica TEXT,
        name_org_politica TEXT,
        url_org_politica TEXT,
        url_ruta_plan_gobierno TEXT,
        url_symbol TEXT,
        num_votos INTEGER,
        num_porc REAL,
        url_archivo_plan_gob TEXT,
        method_http TEXT,
        tipo_link_plan TEXT,

        PRIMARY KEY (
            id_eleccion,
            id_location_req,
            id_group_eleccion,
            id_org_politica
        )
    );
    """)

    conn.commit()


create_tables()

with httpx.Client(timeout=1.0) as client:
    for _, row in procesos_electorales.iterrows():
        try:
            response = post_result(row, client)
            procesar_respuesta(conn, row, response)
        except Exception as e:
            print("ERROR:", row["id_eleccion"], row["id_location_req"], e)
