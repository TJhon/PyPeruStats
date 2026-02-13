from dataclasses import dataclass
from typing import Literal, Optional

SearchType = Literal["code", "description"]


@dataclass
class SearchTextStep:
    query: str
    search_type: SearchType = "code"
    # select_row_text: Optional[list[str]] = []
    select_row_text: Optional[str] = None
    # sele

    def __post_init__(self):
        if self.query is None:
            raise ValueError("La query no puede ser `None`")


@dataclass
class Step:
    name: Optional[str] = None
    click_bttn: Optional[str] = None
    select_row_text: Optional[str] = None
    desc: Optional[str] = None
    save_group: bool = False
    extras: Optional[dict] = None
    post_step: Optional[SearchTextStep] = None

    def __post_init__(self):
        if self.save_group and self.name is None:
            raise ValueError(
                "El guardado secuencial necesita (`save_group`) necesita un `name` no Nulo "
            )
