import sqlite3
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# import os
from perustats.infogob.constants import (
    BASE_URL,
    URL_LISTAR_DISTRITOS,
    URL_LISTAR_PROVINCIAS,
    URL_RESULTADOS_ELECCION,
)


def get_token(soup):
    token = soup.select_one("#key").get("value")
    return token


def build_payload(istr=None, token=None):
    return {"istrParameters": istr, "token": token}


BASE_PATH = Path("./data/infogob/temp/locations")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def csv_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


session = requests.Session()
_ = session.get(BASE_URL, timeout=1)

TOKEN = get_token(BeautifulSoup(_.content, "html.parser"))

conn = sqlite3.connect("./data/infogob/db.db")

procesos_electorales = pd.read_sql(
    "select id_eleccion, id_group_eleccion, istr_value, n_level, name_eleccion from procesos_electorales where n_level > 0",
    con=conn,
).drop_duplicates()


def listar_regiones(eleccion: dict):
    id_group_eleccion = eleccion.get("id_group_eleccion")
    id_eleccion = eleccion.get("id_eleccion")
    prev_istr = eleccion.get("istr_value")

    istr = f"{prev_istr}{id_eleccion}@{id_group_eleccion}"
    params = {"istrParameters": istr}
    payload = {"token": TOKEN}
    # print(params, payload)
    r = session.post(URL_RESULTADOS_ELECCION, params=params, json=payload)
    regiones_soup = BeautifulSoup(r.content, "html.parser")
    # print(regiones_soup)
    regiones_opt = regiones_soup.select_one("#CandidatosResultados").find_all("option")[
        1:
    ]
    regiones = [
        dict(id_region=opt.get("value"), region=opt.get_text(strip=True))
        for opt in regiones_opt
    ]
    return regiones


def listar_sub_loc(proc_electoral, location, name="provincia"):
    if name == "provincia":
        id_father = "id_region"
    elif name == "distrito":
        id_father = "id_provincia"
    istr_parameter_provincia = (
        f"{proc_electoral.get('id_eleccion')}@{location.get(id_father)}"
    )
    payload_region = build_payload(istr_parameter_provincia, TOKEN)
    # print(payload_region)
    if name == "provincia":
        elecciones = session.post(
            URL_LISTAR_PROVINCIAS, data=payload_region, timeout=10
        )
    elif name == "distrito":
        elecciones = session.post(URL_LISTAR_DISTRITOS, data=payload_region, timeout=10)

    data = elecciones.json().get("Data")
    data = data[1:]
    data = [
        {
            **proc_electoral,
            f"name_{name}": eleccion.get("Text").title(),
            f"id_{name}": eleccion.get("Value"),
        }
        for eleccion in data
    ]
    return data


#########
# Regional
#########

ensure_dir(BASE_PATH / "regional")

regiones_all = procesos_electorales.query("n_level == 1")

for idx, row in regiones_all.iterrows():
    file_path = BASE_PATH / "regional" / f"reg_{idx:04d}.csv"

    if csv_exists(file_path):
        continue

    try:
        data = listar_regiones(row)
        if not data:
            continue

        df = pd.DataFrame(data)

        for col, val in row.items():
            df[col] = val
        df.to_csv(file_path, index=False)

    except Exception as e:
        print(f"[REG] Error {idx}: {e}")


##########
# provincial
##########

ensure_dir(BASE_PATH / "provincial")

procesos_prov = procesos_electorales.query("n_level == 2")

for p_idx, proc in procesos_prov.iterrows():
    try:
        regiones = listar_regiones(proc)
    except:
        continue

    for r_idx, reg in enumerate(regiones):
        region_name = reg["region"].replace(" ", "_").upper()
        file_path = BASE_PATH / "provincial" / f"prov_{p_idx:04d}_{region_name}.csv"

        if csv_exists(file_path):
            continue

        try:
            data = listar_sub_loc(proc, reg, name="provincia")
            if not data:
                continue

            df = pd.DataFrame(data)
            df.assign(**reg).to_csv(file_path, index=False)

        except Exception as e:
            print(f"[PROV] {region_name} | {e}")


########
# distrital
##########


ensure_dir(BASE_PATH / "distrital")

procesos_dist = procesos_electorales.query("n_level == 3")

for p_idx, proc in procesos_dist.iterrows():
    try:
        regiones = listar_regiones(proc)
    except:
        continue

    for reg in regiones:
        try:
            provincias = listar_sub_loc(proc, reg, name="provincia")
        except:
            continue

        for prov in provincias:
            region = reg["region"].replace(" ", "_").upper()
            provincia = prov["name_provincia"].replace(" ", "_").upper()

            file_path = (
                BASE_PATH / "distrital" / f"dist_{p_idx:04d}_{region}_{provincia}.csv"
            )

            if csv_exists(file_path):
                continue

            try:
                dists = listar_sub_loc(proc, prov, name="distrito")
                if not dists:
                    continue

                df = pd.DataFrame(dists)
                df.assign(**prov, **reg).to_csv(file_path, index=False)

            except Exception:
                print(f"[DIST] {region}-{provincia} | {Exception}")
