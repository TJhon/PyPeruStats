"""
Utility functions for INEI Microdatos Fetcher.
"""

import hashlib
import re
import sqlite3
import subprocess
import unicodedata
import zipfile
from pathlib import Path
from urllib.parse import quote

import pandas as pd
from bs4 import BeautifulSoup

from .constants import (
    BASE_URL,
    CACHE_MICRODATOS,
    COLS_PROGRESS,
    SESSION_COOKIE,
    SURVEYS,
    USER_AGENT,
)


def get_modules_details(survey, year, periodo, conn: sqlite3.Connection):
    query = f"""
    SELECT * FROM {CACHE_MICRODATOS}
    WHERE survey = ? AND year = ? AND periodo = ?
        """
    try:
        df_cache = pd.read_sql(query, conn, params=(survey, year, periodo))
        if not df_cache.empty:
            return df_cache
    except Exception:
        pass
    df = get_survey_details(survey=survey, year=year, periodo=periodo)
    df.to_sql(CACHE_MICRODATOS, con=conn, index=False)
    return df


def create_environment(survey: str, master_directory: str, referrer_sql=None):
    master_directory = Path(master_directory) / survey

    zips_directory = master_directory / "0_zips"
    unzipped_directory = master_directory / "1_unzipped"
    organized_directory = master_directory / "2_organized"

    dirs = dict(
        zips=zips_directory,
        unzip=unzipped_directory,
        organized=organized_directory,
    )
    for key, directory in dirs.items():
        directory.mkdir(parents=True, exist_ok=True)
    if referrer_sql is None:
        referrer_sql = "referrer.sql"
    sqlite_path = master_directory / referrer_sql
    conn = sqlite3.connect(sqlite_path)
    return dirs, conn


def slugify(text: str) -> str:
    """
    Convert text to a safe format for filenames without accents or special characters.

    Args:
        text: The text to slugify

    Returns:
        Slugified text in lowercase with underscores
    """
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s\-]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text.lower()


def url_encode_survey_name(name: str) -> str:
    """
    URL-encode a survey name for use in requests.

    Args:
        name: The raw survey name

    Returns:
        URL-encoded survey name
    """
    return quote(name, encoding="iso-8859-1")


def is_zip_valid(path: str) -> bool:
    """
    Check if a ZIP file is valid and not corrupted.

    Args:
        path: Path to the ZIP file

    Returns:
        True if the ZIP file is valid, False otherwise
    """
    try:
        with zipfile.ZipFile(path, "r") as zip_file:
            bad_file = zip_file.testzip()
            return bad_file is None
    except zipfile.BadZipFile:
        return False


def html_to_dataframe(html: str) -> pd.DataFrame:
    """
    Convert INEI response HTML to DataFrame with dynamically detected formats.

    Args:
        html: HTML content from INEI response

    Returns:
        DataFrame containing parsed module information
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table").find("table")
    if table is None:
        return pd.DataFrame()
    rows = table.find_all("tr")
    if len(rows) <= 1:
        return pd.DataFrame()

    data = []
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue

        number = cols[0].get_text(strip=True)
        try:
            year = int(cols[1].get_text(strip=True))
        except:
            year = None
        period = cols[2].get_text(strip=True)
        survey_code = cols[3].get_text(strip=True)
        survey_name = cols[4].get_text(strip=True)
        try:
            module_code = int(cols[5].get_text(strip=True))
        except:
            module_code = None
        module_name = cols[6].get_text(strip=True)
        info_sheet = cols[7].find("a")["href"] if cols[7].find("a") else None

        # Detect available formats
        formats = {"spss": None, "stata": None, "csv": None, "dbf": None}
        for cell in cols[8:]:
            link = cell.find("a")
            if not link or not link.get("href"):
                continue
            href = link["href"]
            title = (link.get("title") or "").lower()
            if "spss" in title or "/SPSS/" in href:
                formats["spss"] = href
            elif "stata" in title or "/STATA/" in href:
                formats["stata"] = href
            elif "csv" in title or "/CSV/" in href:
                formats["csv"] = href
            elif "dbf" in title or "/DBF/" in href:
                formats["dbf"] = href

        data.append(
            {
                "number": number,
                "year_ref": year,
                "period_ref": period,
                "survey_code": survey_code,
                "survey_name": survey_name,
                "module_code": module_code,
                "module_name": module_name,
                "info_sheet": info_sheet,
                **formats,
            }
        )
    return pd.DataFrame(data)


def extract_periodo_value(html: str, periodo="anual") -> str | None:
    """
    Se extrae los periodos/regiones disponibles de los "anios" y se seleccioa un tipo (por defecto anual)
    """
    soup = BeautifulSoup(html, "html.parser")
    options = soup.find_all("option")

    for opt in options:
        text = opt.get_text(strip=True).lower()

        if periodo == "anual" and "anual" in text.lower():
            return opt.get("value")

        if periodo == "trimestre" and "trimestre" in text.lower():
            return opt.get("value")

    return None


def get_period_value(survey: str, year: int, periodo="anual") -> str:
    """
    Execute curl request to fetch survey data from INEI.

    Args:
        survey: Survey type (enaho, endes, enapres)
        year: Year to fetch
        quarter: Optional quarter override

    Returns:
        HTML response from INEI

    Raises:
        ValueError: If survey type is not supported
    """
    config = SURVEYS.get(periodo).get(survey)

    encoded_name = url_encode_survey_name(config["name"])

    data_raw = f"bandera=1&_cmbEncuesta={encoded_name}&_cmbAnno={year}&_cmbEncuesta0={encoded_name}"

    url = BASE_URL.get("consulta")
    cmd = [
        "curl",
        "-s",
        f"{url}/CambiaAnio.asp",
        "-H",
        "Accept: */*",
        "-H",
        "Accept-Language: es,en;q=0.9",
        "-H",
        "Connection: keep-alive",
        "-H",
        "Content-Type: application/x-www-form-urlencoded",
        "-b",
        SESSION_COOKIE,
        "-H",
        f"Origin: {url}",
        "-H",
        f"Referer: {url}/Consulta_por_Encuesta.asp",
        "-H",
        "Sec-Fetch-Dest: empty",
        "-H",
        "Sec-Fetch-Mode: cors",
        "-H",
        "Sec-Fetch-Site: same-origin",
        "-H",
        f"User-Agent: {USER_AGENT}",
        "-H",
        'sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Opera";v="124"',
        "-H",
        "sec-ch-ua-mobile: ?0",
        "-H",
        'sec-ch-ua-platform: "Windows"',
        "--data-raw",
        data_raw,
    ]
    # print(cmd)
    result = subprocess.run(cmd, capture_output=True)
    html = result.stdout.decode("utf-8", errors="ignore")
    period = extract_periodo_value(html, periodo=periodo)
    return period


def get_survey_details(survey: str, year: int, periodo: str = "anual") -> pd.DataFrame:
    """
    Execute curl request to fetch survey data from INEI.

    Args:
        survey: Survey type (enaho, endes, enapres, ...)
        year: Year to fetch

    Returns:
        HTML response from INEI

    Raises:
        ValueError: If survey type is not supported
    """
    SURVEYS_CONFIG = SURVEYS.get(periodo)
    if survey not in SURVEYS_CONFIG.keys():
        raise ValueError(f"Survey not supported: {survey}")

    config = SURVEYS_CONFIG[survey]
    quarter = get_period_value(survey, year, periodo)
    encoded_name = url_encode_survey_name(config["name"])

    data_raw = (
        f"bandera=1&_cmbEncuesta={encoded_name}&_cmbAnno={year}&_cmbTrimestre={quarter}"
    )
    url = BASE_URL.get("consulta")

    cmd = [
        "curl",
        "-s",
        f"{url}/cambiaPeriodo.asp",
        "-H",
        "Accept: */*",
        "-H",
        "Accept-Language: es,en;q=0.9",
        "-H",
        "Connection: keep-alive",
        "-H",
        "Content-Type: application/x-www-form-urlencoded",
        "-b",
        SESSION_COOKIE,
        "-H",
        f"Origin: {url}",
        "-H",
        f"Referer: {url}/Consulta_por_Encuesta.asp",
        "-H",
        "Sec-Fetch-Dest: empty",
        "-H",
        "Sec-Fetch-Mode: cors",
        "-H",
        "Sec-Fetch-Site: same-origin",
        "-H",
        f"User-Agent: {USER_AGENT}",
        "-H",
        'sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Opera";v="124"',
        "-H",
        "sec-ch-ua-mobile: ?0",
        "-H",
        'sec-ch-ua-platform: "Windows"',
        "--data-raw",
        data_raw,
    ]
    result = subprocess.run(cmd, capture_output=True)
    df = html_to_dataframe(result.stdout.decode("utf-8", errors="ignore"))
    df["survey"] = survey
    df["year"] = year
    df["periodo"] = periodo
    df = set_default_progress(df)
    return df


def to_curl_cmd(cmd: list[str]) -> str:
    out = []
    for c in cmd:
        if " " in c or '"' in c:
            c = c.replace('"', r"\"")
            c = f'"{c}"'
        out.append(c)
    return " ^\n  ".join(out)


def _file_hash(path: Path, chunk_size: int = 1 << 20) -> str:
    """Compute SHA-256 hash for a file (streamed, memory-safe)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def set_default_progress(df):
    for col in COLS_PROGRESS:
        df[col] = False
    return df
