import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .ubigeos import BASE_URL, ID_ELECCION, get_json

with open("./data/onpe/distritos_ubigeos.json", "r", encoding="utf-8") as f:
    data_list = json.load(f)

data = pd.DataFrame(data_list)


fecha_min = datetime.now().strftime("%Y-%m-%d %H")


def fetch_totales(ubigeo):
    name = f"./data/onpe/result/{fecha_min}/{ubigeo.get('name_dep')}/{ubigeo.get('ubigeo_dist')}.json"
    Path(name).parent.mkdir(parents=True, exist_ok=True)

    if os.path.exists(name):
        return

    data = {
        "idEleccion": ID_ELECCION,
        "tipoFiltro": "ubigeo_nivel_03",
        "idAmbitoGeografico": ubigeo.get("ambito"),
        "idUbigeoDepartamento": ubigeo.get("ubigeo_dep"),
        "idUbigeoProvincia": ubigeo.get("ubigeo_prov"),
        "idUbigeoDistrito": ubigeo.get("ubigeo_dist"),
    }
    totales = get_json(f"{BASE_URL}/resumen-general/totales", data)
    resultados = get_json(f"{BASE_URL}/resumen-general/participantes", data)

    data_ref = {
        "totales": totales,
        "resultados": resultados,
        "ubigeo": data,
        "actualizacion": fecha_min,
    }

    with open(name, "w", encoding="utf-8") as f:
        json.dump(data_ref, f, ensure_ascii=False, indent=2)

    return data_ref


for _, row in tqdm(data.iterrows(), total=len(data)):
    try:
        a = fetch_totales(row)
    except Exception:
        pass
