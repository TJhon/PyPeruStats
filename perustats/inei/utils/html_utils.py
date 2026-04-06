"""
HTML parsing utilities for INEI portal responses.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup

from ..surveys.registry import Survey


def html_to_dataframe(html: str) -> pd.DataFrame:
    """
    Parse the INEI module-listing HTML response into a tidy DataFrame.

    Returns an empty DataFrame when the page contains no table or no data rows.
    """
    soup = BeautifulSoup(html, "html.parser")
    outer = soup.find("table")
    if outer is None:
        return pd.DataFrame()
    table = outer.find("table")
    if table is None:
        return pd.DataFrame()

    rows = table.find_all("tr")
    if len(rows) <= 1:
        return pd.DataFrame()

    records = []
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue

        try:
            year = int(cols[1].get_text(strip=True))
        except (ValueError, TypeError):
            year = None

        try:
            module_code = int(cols[5].get_text(strip=True))
        except (ValueError, TypeError):
            module_code = None

        formats: dict[str, Optional[str]] = {
            "spss": None,
            "stata": None,
            "csv": None,
            "dbf": None,
        }
        for cell in cols[8:]:
            link = cell.find("a")
            if not link or not link.get("href"):
                continue
            href: str = link["href"]
            title = (link.get("title") or "").lower()
            if "spss" in title or "/SPSS/" in href:
                formats["spss"] = href
            elif "stata" in title or "/STATA/" in href:
                formats["stata"] = href
            elif "csv" in title or "/CSV/" in href:
                formats["csv"] = href
            elif "dbf" in title or "/DBF/" in href:
                formats["dbf"] = href

        info_link = cols[7].find("a")
        records.append(
            {
                "number": cols[0].get_text(strip=True),
                "year_ref": year,
                "period_ref": cols[2].get_text(strip=True),
                "survey_code": cols[3].get_text(strip=True),
                "survey_name": cols[4].get_text(strip=True),
                "module_code": module_code,
                "module_name": cols[6].get_text(strip=True),
                "info_sheet": info_link["href"] if info_link else None,
                **formats,
            }
        )

    return pd.DataFrame(records)


def extract_period_value(html: str, survey: Survey) -> Optional[str]:
    """
    Find the <option> value that corresponds to *survey.period* in *html*.

    The INEI page exposes a period/region selector whose option texts vary by
    survey (e.g. "Anual", "Único", "Panel").  We match against the aliases
    stored in ``survey.period_aliases``.
    """
    soup = BeautifulSoup(html, "html.parser")
    aliases = survey.period_aliases  # e.g. ["anual", "unico"]

    for opt in soup.find_all("option"):
        text = opt.get_text(strip=True).lower()
        if text in aliases:
            return opt.get("value")
        for alias in aliases:
            if alias in text:
                return opt.get("value")

    return None
