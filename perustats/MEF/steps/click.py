"metodos que simulan la iteraccion con la tabla presente y botones presentes en la UI del MEF"

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
    """
    rows: mediante regex se busca entre las filas dentro de la tabla "data" si contienen alguno elemento dentro del row y sirve para filtrar solo esas filas, una lista vacia representa que se recorrera todas las filas de "data"
    """

    rows: list[str] = field(default_factory=list)
    on_missing = OnMissing.RECORD


@dataclass
class ClickBtn:
    """
    button: id del boton al que se dara "click" (uno puede  utilizar string que sale despues de inspeccionar la pagina de la web (f12) luego redirigir el mouse al boton que se quiere simular, ubicar la fila y extraer la propiedad name de la etiqueta))
    as_column: permite generar columas adicionales que peremiten identificar correctamente al workflow realizado
    name: es el nombre de la columna que se creara, para identificar (se genera automaticamente basandose en el button)
    """

    button: str
    as_column: bool = True
    name: str = field(init=False)

    def __post_init__(self):
        if "Btn" in self.button:
            self.name = self.button.split("Btn")[-1]
        else:
            self.name = self.button

    def __repr__(self):
        return f"ClickBtn(name={self.name})"


@dataclass
class SavePartial:
    """
    ---No implementado aun
    filename_prefix: si es diferente a None, entonces desde ese punto guardara progresivamente por las iteracciones de las filas (util cuando se cae la pagina del mef)
    """

    filename_prefix: str | None = None


@dataclass
class Search:
    """
    Cuando la data es inmensa (supere las 400 filas) la UI de consulta amigable permite buscar mediante descripcion o codigo
    query: lo que se pondria en el recuadro de busqueda
    method: por defectto description, si se dara click a descripcion o codigo
    """

    query: str = None
    method: Literal["description", "code"] = "description"
