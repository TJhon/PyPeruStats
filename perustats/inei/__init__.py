"""
perustats.inei
==============

Download and organize INEI microdata (microdatos).

Quick start
-----------
>>> from perustats.inei import INEIFetcher, registry
>>>
>>> # See all available surveys
>>> registry.list_codes()
>>>
>>> # Register a new survey (no other file needs changing)
>>> from perustats.inei.surveys import Survey
>>> registry.register(Survey("enniv", "Encuesta Nacional de Niveles de Vida", "anual"))
>>>
>>> # Download ENAHO 2020-2022, Stata format preferred
>>> fetcher = INEIFetcher(
...     survey="enaho",
...     years=range(2020, 2023),
...     master_directory="./datos",
... )
>>> fetcher.fetch_modules().download(module_codes=[1, 2, 3]).organize(organize_by="year")
"""

from .fetcher import INEIFetcher
from .surveys.registry import Survey, registry

__all__ = ["INEIFetcher", "Survey", "registry"]
