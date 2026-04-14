from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class OnMissing(str, Enum):
    SKIP = "skip"
    RECORD = "record"  # ← default recomendado
    RAISE = "raise"


@dataclass
class Rows:
    rows: list[str] = field(default_factory=list)
    on_missing = OnMissing.RECORD


@dataclass
class ClickBtn:
    button: str


@dataclass
class SavePartial:
    filename_prefix: str | None = None


@dataclass
class Search:
    query: str = None
    method: Literal["description", "code"] = "description"
