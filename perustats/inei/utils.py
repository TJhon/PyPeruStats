"""
Utility functions for INEI Microdatos Fetcher.
"""

import unicodedata
import re
import zipfile
import subprocess
from urllib.parse import quote
from pathlib import Path
from typing import Optional
import pandas as pd
from bs4 import BeautifulSoup
from .constants import SURVEYS_CONFIG, SESSION_COOKIE, USER_AGENT, BASE_URL
from rich import print
import hashlib


# Encuesta%20Demogr%E1fica%20y%20de%20Salud%20Familiar%20-%20ENDES
# Encuesta%20Demogr%C3%A1fica%20y%20de%20Salud%20Familiar%20-%20ENDES&_cmbAnno=2011&_cmbTrimestre=5'
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
    table = soup.find("table")
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
                "year": year,
                "period": period,
                "survey_code": survey_code,
                "survey_name": survey_name,
                "module_code": module_code,
                "module_name": module_name,
                "info_sheet": info_sheet,
                **formats,
            }
        )
    return pd.DataFrame(data)


def execute_curl_survey_request(
    survey: str, year: int, quarter: Optional[str] = None
) -> str:
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
    if survey not in SURVEYS_CONFIG:
        raise ValueError(f"Survey not supported: {survey}")

    config = SURVEYS_CONFIG[survey]
    quarter = quarter or config["default_quarter"]
    encoded_name = url_encode_survey_name(config["name"])

    data_raw = (
        f"bandera=1&_cmbEncuesta={encoded_name}&_cmbAnno={year}&_cmbTrimestre={quarter}"
    )

    cmd = [
        "curl",
        "-s",
        f"{BASE_URL}/cambiaPeriodo.asp",
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
        f"Origin: {BASE_URL}",
        "-H",
        f"Referer: {BASE_URL}/Consulta_por_Encuesta.asp",
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
    return result.stdout.decode('utf-8', errors='ignore')


def _file_hash(path: Path, chunk_size: int = 1 << 20) -> str:
    """Compute SHA-256 hash for a file (streamed, memory-safe)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()
