"""
ModuleFetcher: scrapes the INEI portal to obtain the list of available
modules (with their download URLs) for a given survey + year combination.

This class is intentionally free of any download or file-system logic so it
can be tested or used independently.
"""

from __future__ import annotations

import pandas as pd

from .constants import BASE_URL
from .surveys.registry import Survey
from .utils.html_utils import extract_period_value, html_to_dataframe
from .utils.http_utils import fetch_html, url_encode_survey_name


class ModuleFetcher:
    """
    Retrieves the module table for a single (survey, year) pair from the
    INEI microdata portal.

    Parameters
    ----------
    survey:
        A :class:`~perustats.inei.surveys.registry.Survey` instance.
    """

    def __init__(self, survey: Survey) -> None:
        self.survey = survey

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def fetch(self, year: int) -> pd.DataFrame:
        """
        Return a tidy DataFrame of available modules for *year*.

        The DataFrame will contain at least: ``module_code``, ``module_name``,
        ``year_ref``, ``period_ref``, ``spss``, ``stata``, ``csv``, ``dbf``.
        """
        period_value = self._get_period_value(year)
        df = self._get_modules_table(year, period_value)
        df["survey"] = self.survey.code
        df["year"] = year
        df["periodo"] = self.survey.period
        # Initialise progress columns to None / False
        for col in ("url", "path_download", "path_extract", "path_organized"):
            df[col] = None
        return df

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _get_period_value(self, year: int) -> str | None:
        """
        POST to the INEI 'CambiaAnio' endpoint and extract the period/quarter
        value that matches this survey's period type.
        """
        encoded_name = url_encode_survey_name(self.survey.name)
        # ENAHO uses "2" as the encuesta0 parameter; all others use the name
        encuesta0 = "2" if self.survey.code.startswith("enaho") else encoded_name

        data = (
            f"bandera=1"
            f"&_cmbEncuesta={encoded_name}"
            f"&_cmbAnno={year}"
            f"&_cmbEncuesta0={encuesta0}"
        )
        # print(data)
        url = BASE_URL["consulta"] + "/CambiaAnio.asp"
        html = fetch_html(url, data)
        return extract_period_value(html, self.survey)

    def _get_modules_table(self, year: int, period_value: str | None) -> pd.DataFrame:
        """
        POST to the INEI 'cambiaPeriodo' endpoint and parse the module table.
        """
        encoded_name = url_encode_survey_name(self.survey.name)
        data = (
            f"bandera=1"
            f"&_cmbEncuesta={encoded_name}"
            f"&_cmbAnno={year}"
            f"&_cmbTrimestre={period_value}"
        )
        url = BASE_URL["consulta"] + "/cambiaPeriodo.asp"
        html = fetch_html(url, data)
        return html_to_dataframe(html)
