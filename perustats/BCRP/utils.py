import re
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import requests

from perustats.BCRP.archive.constants import DB_PATH
from perustats.BCRP.models import BASE_API_URL


def _format_date_for_frequency(
    date_str: str, frequency: str, fmt: str = "%Y-%m-%d"
) -> str:
    """
    Convert a YYYY-MM-DD date string to the format expected by the BCRP API
    for the given frequency.

    Parameters
    ----------
    date_str:
        Date in ``fmt`` format (default ``%Y-%m-%d``).
    frequency:
        One of ``'D'``, ``'M'``, ``'Q'``, ``'A'``.
    fmt:
        strptime format of *date_str*.

    Returns
    -------
    str
        Date string formatted for the BCRP API endpoint.

    Examples
    --------
    >>> _format_date_for_frequency("2023-06-15", "D")
    '2023-06-15'
    >>> _format_date_for_frequency("2023-06-15", "M")
    '2023-06'
    >>> _format_date_for_frequency("2023-06-15", "Q")
    '2023-2'
    >>> _format_date_for_frequency("2023-06-15", "A")
    '2023'
    """
    dt = datetime.strptime(date_str, fmt)
    if frequency == "D":
        return dt.strftime("%Y-%m-%d")
    if frequency == "M":
        return dt.strftime("%Y-%m")
    if frequency == "Q":
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-{quarter}"
    if frequency == "A":
        return dt.strftime("%Y")
    raise ValueError(f"Unknown frequency: {frequency!r}")


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
                "date_inicio": clean_text(tds[3].text),
                "date_fin": clean_text(tds[4].text),
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
        columns include 'date' and series names with numeric values

    Note:
        - Converts Spanish month abbreviations to English
        - Converts series values to numeric, handling errors gracefully
    """
    series_names = [serie["name"] for serie in json["config"]["series"]]
    # series_names = codes
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
    df = df.sort_values("date")
    return df


def apply_date_format(
    df: pd.DataFrame,
    frequency: str,
) -> pd.DataFrame:
    """
    Parse the ``date`` column using the format appropriate for *frequency*.

    Parameters
    ----------
    df:
        DataFrame with a ``date`` string column as returned by
        :func:`json_to_dataframe`.
    frequency:
        One of ``'D'``, ``'M'``, ``'Q'``, ``'A'``.
    quarter_to_timestamp:
        When ``True`` (default), quarterly periods are converted to the
        end-of-quarter ``Timestamp``. When ``False`` they remain
        ``pd.Period`` objects.

    Returns
    -------
    pandas.DataFrame
        Same DataFrame with ``date`` replaced by parsed dates and set as the
        index.
    """
    df = df.copy()

    frequency = frequency.upper()

    if frequency == "Q":
        # API returns e.g. "Q1.23" → normalise to "23Q1" for PeriodIndex
        df["date"] = pd.PeriodIndex(
            df["date"].str.replace(r"Q(\d)\.(\d{2})", r"\2Q\1", regex=True),
            freq="Q",
        )

        df["yq"] = df["date"].astype("str")
        df["date"] = df["date"].dt.to_timestamp(how="end")

    elif frequency == "A":
        df["date"] = pd.to_datetime(df["date"], format="%Y")

    elif frequency == "M":
        df["date"] = pd.to_datetime(df["date"], format="%b.%Y")

    elif frequency == "D":
        df["date"] = pd.to_datetime(df["date"], format="%d.%b.%y")

    else:
        raise ValueError(f"Unknown frequency: {frequency!r}")

    # df = df.set_index("date")
    df = df.sort_values("date")
    return df
