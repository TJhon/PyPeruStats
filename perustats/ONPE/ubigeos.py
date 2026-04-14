import json
import os

import requests

ID_ELECCION = 10


BASE_URL = "https://resultadoelectoral.onpe.gob.pe/presentacion-backend"
HEADERS = {
    "accept": "*/*",
    "accept-language": "es,en;q=0.9",
    "content-type": "application/json",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
    "referer": "https://resultadoelectoral.onpe.gob.pe/main/resumen",
}


def get_json(url, params):
    r = requests.get(url, params=params, headers=HEADERS, timeout=2)
    r.raise_for_status()

    data = r.json()

    if not data.get("success"):
        return

    result = data.get("data")
    return result


def parse_response(data: list, sufix="dep", add_dict={}):
    r = [
        {
            f"ubigeo_{sufix}": dep.get("ubigeo"),
            f"name_{sufix}": dep.get("nombre"),
            **add_dict,
        }
        for dep in data
    ]
    return r


def fetch_dep(ambito=1) -> list:
    r = get_json(
        f"{BASE_URL}/ubigeos/departamentos",  # departamentos/continendtes
        dict(idEleccion=ID_ELECCION, idAmbitoGeografico=ambito),
    )
    r = parse_response(r, "dep", {"ambito": ambito})
    return r


def fetch_prov(dep_ubigeo, ambito=1) -> list:
    r = get_json(
        f"{BASE_URL}/ubigeos/provincias",  # paises/provincias
        dict(
            idEleccion=ID_ELECCION,
            idAmbitoGeografico=ambito,
            idUbigeoDepartamento=dep_ubigeo.get("ubigeo_dep"),
        ),
    )
    r = parse_response(r, "prov", dep_ubigeo)

    return r


def fetch_distritos(prov_ubigeo, ambito=1) -> list:
    r = get_json(
        f"{BASE_URL}/ubigeos/distritos",  # "departamentos"/distritos
        dict(
            idEleccion=ID_ELECCION,
            idAmbitoGeografico=ambito,
            idUbigeoProvincia=prov_ubigeo.get("ubigeo_prov"),
        ),
    )
    r = parse_response(r, "dist", prov_ubigeo)

    return r


CACHE_DIR = "./data/onpe/cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def load_cache(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cache(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


distritos_ubigeos = []

distritos_ubigeos = []
for ambito in [1, 2]:
    from tqdm import tqdm

    # Caché departamentos
    dep_cache = f"{CACHE_DIR}/ambito_{ambito}_dep.json"
    departamentos = (
        load_cache(dep_cache)
        or save_cache(dep_cache, fetch_dep(ambito=ambito))
        or load_cache(dep_cache)
    )

    for dep in tqdm(departamentos, desc=f"Ámbito {ambito} - Departamentos"):
        dep_code = dep.get("name_dep")

        # Caché provincias
        prov_cache = f"{CACHE_DIR}/ambito_{ambito}_{dep_code}_prov.json"
        provincias = (
            load_cache(prov_cache)
            or save_cache(prov_cache, fetch_prov(dep_ubigeo=dep, ambito=ambito))
            or load_cache(prov_cache)
        )

        for prov in tqdm(
            provincias,
            desc=f"Ámbito {ambito} - {dep.get('name_dep')} - Provincias",
            leave=False,
        ):
            prov_code = prov.get("name_prov")
            # print(prov_code)

            # Caché provincias
            dist_cache = f"{CACHE_DIR}/ambito_{ambito}_{dep_code}_{prov_code}.json"
            distritos = (
                load_cache(dist_cache)
                or save_cache(dist_cache, fetch_distritos(prov, ambito=ambito))
                or load_cache(dist_cache)
            )

            distritos_ubigeos.extend(distritos)

with open("./data/onpe/distritos_ubigeos.json", "w", encoding="utf-8") as f:
    json.dump(distritos_ubigeos, f, ensure_ascii=False, indent=2)
