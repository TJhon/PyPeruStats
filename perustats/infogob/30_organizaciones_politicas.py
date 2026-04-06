import sqlite3

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from perustats.infogob.constants import BASE_URL

conn = sqlite3.connect("./data/infogob/db.db")


def create_table():
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS org_politica (
        url_org_politica TEXT,
        title_partido TEXT,
        tipo TEXT,
        ambito TEXT,
        estado TEXT,
        direccion TEXT,
        fecha_inscripcion TEXT,
        fecha_cancelacion TEXT
        );
        """
    )
    conn.commit()


create_table()

done = pd.read_sql(
    """
    SELECT url_org_politica as url 
    FROM org_politica
    """,
    con=conn,
)["url"].values

url_org_politica = pd.read_sql(
    """
    SELECT DISTINCT url_org_politica 
    FROM resultados_by_org_politica  
    """,
    con=conn,
).query("url_org_politica not in @done")


urls = url_org_politica["url_org_politica"]


def get_info_partido(url_):
    url_org = BASE_URL + url_
    r = httpx.request("get", url_org, timeout=1)
    soup = BeautifulSoup(r.text, "html.parser")
    datos_partido = soup.find("div", {"class": "datos-partido"})
    results = datos_partido.find_all("span", {"class": "control"})
    results = [r.get_text(strip=True) for r in results]
    title = soup.find("div", {"class": "nombrePartido"}).get_text(strip=True)
    ref_erencia = [
        {
            "url_org_politica": url_,
            "title_partido": title,
            "tipo": results[0],
            "estado": results[1],
            "fecha_inscripcion": results[2],
            "ambito": results[3],
            "direccion": results[4],
            "fecha_cancelacion": results[5],
        }
    ]

    df_n = pd.DataFrame(ref_erencia)
    df_n.to_sql("org_politica", con=conn, if_exists="append", index=False)
    return df_n


for url_ref in tqdm(urls, desc="organizaciones politicas"):
    try:
        get_info_partido(url_ref)
    except:
        pass
