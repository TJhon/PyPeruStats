import sqlite3
import unicodedata
from pathlib import Path

import pandas as pd
import polars as pl

BASE = Path("./data/infogob/temp/locations")

csv_files = list(BASE.rglob("*.csv"))

dfs = []
for f in csv_files:
    try:
        dfs.append(pl.read_csv(f))
    except Exception as e:
        print(f"Error leyendo {f}: {e}")

locations_raw = pl.concat(dfs, how="diagonal")

locations_raw = locations_raw.with_columns(
    pl.when(pl.col("id_distrito").is_not_null())
    .then(pl.col("id_distrito"))
    .when(pl.col("id_provincia").is_not_null())
    .then(pl.col("id_provincia"))
    .otherwise(pl.col("id_region"))
    .alias("id_location_req")
)

locations_raw = locations_raw.with_columns(pl.lit(False).alias("procesado"))


conn = sqlite3.connect("./data/infogob/db.db")

(
    locations_raw.to_pandas().to_sql(
        "procesos_electorales_locations", con=conn, if_exists="replace", index=False
    )
)


locations_raw_pd = locations_raw.to_pandas()


def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def clean_text(series: pd.Series) -> pd.Series:
    return (
        series.dropna()
        .astype(str)
        # quitar acentos y ñ → n
        .apply(strip_accents)
        .str.upper()
        # solo A-Z y 0-9
        .str.replace(r"[^A-Z0-9]", " ", regex=True)
        # colapsar espacios
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def most_common(series: pd.Series):
    s = clean_text(series)
    if s.empty:
        return None
    return s.value_counts().idxmax()


locations: pd.DataFrame = (
    locations_raw_pd.groupby(["id_region", "id_provincia", "id_distrito"], dropna=False)
    .agg(
        region=("region", most_common),
        provincia=("name_provincia", most_common),
        distrito=("name_distrito", most_common),
    )
    .reset_index()
)

locations = locations.assign(ubigeo=None)

locations.to_sql("locations", con=conn)
