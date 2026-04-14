from dataclasses import dataclass, field

from perustats.MEF.v2.constants import buttons as btn
from perustats.MEF.v2.steps.click import ClickBtn, Rows, SavePartial, Search

STEPS = ClickBtn | Rows | SavePartial | Search


@dataclass
class Step:
    rows: Rows  # filtrar filas dentro de la tabla visible
    click: ClickBtn  # action
    save: SavePartial | None = None  # si guardamos el progreso desde este punto
    search: Search | None = (
        None  # accion adicional util cuando la tabla tiene muchisimos registros y se no aparece el elemento (el mef tiene su backen para este tipo de consulta -> busca por descripcion o codigo y actualiza la tabla)
    )


@dataclass
class Workflow:
    steps: list = field(default_factory=list)

    def __post_init__(self):
        self.p_steps = self._parse(self.steps)

    @staticmethod
    def _parse(raw: list[STEPS]) -> list[Step]:
        result = []
        i = 0
        while i < len(raw):
            item = raw[i]

            # Cada bloque debe comenzar con Rows
            if not isinstance(item, Rows):
                raise ValueError(
                    f"Se esperaba Rows en posición {i}, se obtuvo {type(item).__name__}"
                )

            rows = item
            click = save = search = None
            i += 1

            # Consumir los demás tipos del bloque hasta el próximo Rows (o fin)
            while i < len(raw) and not isinstance(raw[i], Rows):
                current = raw[i]
                if isinstance(current, ClickBtn):
                    click = current
                elif isinstance(current, SavePartial):
                    save = current
                elif isinstance(current, Search):
                    search = current
                else:
                    raise ValueError(
                        f"Tipo inesperado en posición {i}: {type(current).__name__}"
                    )
                i += 1

            if click is None:
                raise ValueError(f"Bloque con Rows({rows.rows}) no tiene ClickBtn")

            result.append(Step(rows=rows, click=click, save=save, search=search))

        return result


input = [
    Rows(["total"]),
    ClickBtn(btn.NIVEL_GOBIERNO),
    ###############
    # click en la fila que tenga 'locales' y click en generica
    Rows(["locales"]),
    ClickBtn(btn.GOB_LOCALES_MANCOMUNIDADES),
    ########
    Rows(["municipalidades"]),
    ClickBtn(btn.GENERICA),
    ###############
    Rows(),
    # cuando no se define nada entonces se guarda la informacion de todas las filas y se iterara fila por fila los siguientes pasos
    ClickBtn(btn.DEPARTAMENTO),
    # definimos el save partial para guardar progreso
    SavePartial(filename_prefix="departamento"),
    #############
    # solo estos departamentos
    Rows(["ica", "junin", "piura"]),
    ClickBtn(btn.MUNICIPALIDAD),
    Search("provincial"),
]

output = [
    Step(
        rows=Rows(["total"]),
        click=ClickBtn(btn.NIVEL_GOBIERNO),
    ),
    ###############
    # click en la fila que tenga 'locales' y click en generica
    Step(
        rows=Rows(["locales"]),
        click=ClickBtn(btn.GOB_LOCALES_MANCOMUNIDADES),
    ),
    ########
    Step(
        rows=Rows(["municipalidades"]),
        click=ClickBtn(btn.GENERICA),
    ),
    ###############
    Step(
        rows=Rows(),
        # cuando no se define nada entonces se guarda la informacion de todas las filas y se iterara fila por fila los siguientes pasos
        click=ClickBtn(btn.DEPARTAMENTO),
        # definimos el save partial para guardar progreso
        save=SavePartial(filename_prefix="departamento"),
    ),
    #############
    Step(
        # solo estos departamentos
        rows=Rows(["ica", "junin", "piura"]),
        click=ClickBtn(btn.MUNICIPALIDAD),
        search=Search("provincial"),
    ),
]


if __name__ == "__main__":
    from rich import print

    print(input)

    wk = Workflow(input)
    print(wk.p_steps)
