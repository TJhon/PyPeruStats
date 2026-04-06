"""
Survey model and registry for INEI microdata surveys.

Adding a new survey requires only one line in this file — no Literal, no dict spread.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


SurveyPeriod = Literal["anual", "panel"]
_PERIOD_ALIASES: Dict[str, List[str]] = {
    "anual": ["anual", "unico"],
    "panel": ["panel"],
}


@dataclass(frozen=True)
class Survey:
    """
    Represents a single INEI survey with its metadata.

    Attributes
    ----------
    code:       Short identifier used in the INEI URL (e.g. 'enaho').
    name:       Full Spanish name as expected by the INEI portal.
    period:     Periodicity – 'anual' or 'panel'.
    """

    code: str
    name: str
    period: SurveyPeriod = "anual"

    # ------------------------------------------------------------------ #
    # Convenience helpers                                                  #
    # ------------------------------------------------------------------ #

    @property
    def period_aliases(self) -> List[str]:
        """Lower-case tokens that the INEI <option> element may contain."""
        return _PERIOD_ALIASES.get(self.period, [self.period])

    def __str__(self) -> str:
        return f"{self.code} ({self.period}): {self.name}"


class SurveyRegistry:
    """
    Central store for all known INEI surveys.

    Usage
    -----
    >>> registry.get("enaho")
    Survey(code='enaho', name='Condiciones de Vida y Pobreza - ENAHO', period='anual')

    >>> registry.list_codes()
    ['enaho', 'enaho_panel', 'enapres', 'endes', 'renamu']

    Adding a new survey requires only:
        registry.register(Survey("new_code", "Full Spanish Name", "anual"))
    """

    def __init__(self) -> None:
        self._store: Dict[str, Survey] = {}

    def register(self, survey: Survey) -> "SurveyRegistry":
        if survey.code in self._store:
            raise ValueError(f"Survey '{survey.code}' is already registered.")
        self._store[survey.code] = survey
        return self  # allow chaining

    def get(self, code: str) -> Survey:
        if code not in self._store:
            available = ", ".join(self._store)
            raise KeyError(
                f"Unknown survey code '{code}'. Available codes: {available}"
            )
        return self._store[code]

    def list_codes(self, period: Optional[SurveyPeriod] = None) -> List[str]:
        if period is None:
            return sorted(self._store)
        return sorted(s.code for s in self._store.values() if s.period == period)

    def all(self) -> List[Survey]:
        return list(self._store.values())

    def __contains__(self, code: str) -> bool:
        return code in self._store

    def __repr__(self) -> str:
        lines = [f"  {s}" for s in self._store.values()]
        return "SurveyRegistry(\n" + "\n".join(lines) + "\n)"


# --------------------------------------------------------------------------- #
# Built-in surveys — add yours here with a single line                        #
# --------------------------------------------------------------------------- #

registry = SurveyRegistry()

registry.register(Survey("enaho",       "Condiciones de Vida y Pobreza - ENAHO",                  "anual"))
registry.register(Survey("enaho_panel", "Condiciones de Vida y Pobreza - ENAHO Panel",             "panel"))
registry.register(Survey("enapres",     "Encuesta Nacional de Programas Presupuestales - ENAPRES", "anual"))
registry.register(Survey("endes",       "Encuesta Demográfica y de Salud Familiar - ENDES",        "anual"))
registry.register(Survey("renamu",      "Registro Nacional de Municipalidades - RENAMU",           "anual"))
