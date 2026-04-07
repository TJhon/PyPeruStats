import re
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import requests

from perustats.BCRP.archive.constants import DB_PATH
from perustats.BCRP.models import BASE_API_URL


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def clean_text(text: str) -> str:
    """Limpia tabs, saltos de línea y espacios extra."""
    return re.sub(r"\s+", " ", text).strip()


def parse_series_table(table) -> pd.DataFrame:
    rows = []
    for tr in table.find_all("tr")[1:]:  # saltar el header
        tds = tr.find_all("td")
        if not tds:
            continue

        # Extraer código y link
        codigo_td = tds[1].find("a")
        serie_td = tds[2].find("a")

        rows.append(
            {
                "codigo": clean_text(codigo_td.text) if codigo_td else None,
                "serie": clean_text(serie_td.text) if serie_td else None,
                "fecha_inicio": clean_text(tds[3].text),
                "fecha_fin": clean_text(tds[4].text),
                "url": codigo_td["href"] if codigo_td else None,
                "ultima_act": clean_text(tds[5].text),
            }
        )

    return pd.DataFrame(rows)


def active_codes(metadata: pd.DataFrame, years: int = 2) -> pd.DataFrame:
    """Filtra códigos actualizados en los últimos N años."""
    cutoff = datetime.now() - timedelta(days=365 * years)

    metadata = metadata.copy()
    metadata["ultima_act"] = pd.to_datetime(
        metadata["ultima_act"], dayfirst=True, errors="coerce"
    )
    metadata["activo"] = metadata["ultima_act"].apply(lambda x: int(x >= cutoff))

    return metadata


def get_data_api(codes, start_date, end_date):
    codes = [cd.strip() for cd in codes]
    codes_j = "-".join(codes)
    root_url = BASE_API_URL.format(codes=codes_j, begin=start_date, end=end_date)
    # print(root_url)
    response = requests.get(root_url).json()
    return response


def json_to_df(json, codes):
    """
    Convert BCRP API JSON response to a pandas DataFrame.

    Args:
        json (dict): JSON response from BCRP API

    Returns:
        pandas.DataFrame: DataFrame with time series data,
        columns include 'fecha' and series names with numeric values

    Note:
        - Converts Spanish month abbreviations to English
        - Converts series values to numeric, handling errors gracefully
    """
    series_names = [serie["name"] for serie in json["config"]["series"]]
    series_names = codes
    periods = json["periods"]
    df = pd.DataFrame(
        [
            {"date": period["name"], **dict(zip(series_names, period["values"]))}
            for period in periods
        ]
    )
    meses = {"Ene": "Jan", "Abr": "Apr", "Ago": "Aug", "Set": "Sep", "Dic": "Dec"}
    for mes_es, mes_en in meses.items():
        df["date"] = df["date"].str.replace(mes_es, mes_en)
    for serie in series_names:
        df[serie] = pd.to_numeric(df[serie], errors="coerce")
    return df
