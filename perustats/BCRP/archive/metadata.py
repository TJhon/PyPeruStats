import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from perustats.BCRP.archive.constants import (
    CLASS_DIV_DROPDOWN,
    FREQ,
    FREQ_MAP,
    GROUP_SIZE,
    SERIES_TABLE,
    SERIES_URL,
)
from perustats.BCRP.archive.utils import (
    active_codes,
    clean_text,
    get_connection,
    parse_series_table,
)

all_df = []

for tt in FREQ:
    url = SERIES_URL.format(type=tt)
    r = requests.get(url)

    soup = BeautifulSoup(r.content, "html.parser")
    dropdown = soup.find_all("div", {"class": CLASS_DIV_DROPDOWN})

    for lista in tqdm(dropdown, desc=tt):
        name = lista.find("h2").get_text().strip()
        name = clean_text(name)
        try:
            fuente = lista.find("p", {"class": "fuente"}).get_text()
            fuente = fuente.replace("Fuente: ", "")
        except Exception:
            fuente = None
        table = lista.find("table", {"class": "series"})
        df = parse_series_table(table)
        df["grupo"] = name
        df["fuente"] = fuente
        df["tipo"] = tt
        all_df.append(df)

metadata = pd.concat(all_df, ignore_index=True)
df = active_codes(metadata)


df["_group_idx"] = df.groupby("tipo").cumcount() // GROUP_SIZE + 1


df["tipomap"] = df["tipo"].map(FREQ_MAP)

df["grupo_file"] = (
    "G_" + df["tipomap"] + "_" + df["_group_idx"].astype(str).str.zfill(3)
)

df.drop(columns=["_group_idx", "tipomap"], inplace=True)

conn = get_connection()

df.to_sql(SERIES_TABLE, con=conn)
