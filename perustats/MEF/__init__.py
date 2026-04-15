from perustats.MEF.constants import buttons as BTN
from perustats.MEF.steps.click import ClickBtn, Rows, Search

from .scrapper import MEFScraper

if __name__ == "__main__":
    from rich import print

    base_inicio = [
        Rows(["total"]),
        ClickBtn(BTN.NIVEL_GOBIERNO),
        Rows(["locales"]),
    ]

    bloque_mancomunidades = [
        ClickBtn(BTN.GOB_LOCALES_MANCOMUNIDADES, as_column=False),
        Rows(["municipal"]),
    ]

    bloque_final = [
        ClickBtn(BTN.GENERICA),
        Rows(["deuda publica", "bienes y servicios"]),
        ClickBtn(BTN.DEPARTAMENTO),
        Rows(["ancash", "lima"]),
        ClickBtn(BTN.MUNICIPALIDAD),
    ]

    stp1 = base_inicio + bloque_mancomunidades + bloque_final
    stp3 = base_inicio + bloque_final

    r = MEFScraper(stp1, convert_numeric=False).run(2020)

    # # print("--------------====================\n\n")
    print(r.result)

    r = MEFScraper(stp3, convert_numeric=False).run(2010)

    print(r.result)

    """anterior -> flujo corto"""

    # print(r.config)
    # s = r.initial_session
    # print(s)

    stp2 = [
        Rows(["total"]),
        ClickBtn(BTN.CATEGORIA_PRESUPUESTAL),
        Search("poblacion"),
        Rows(["edu"]),
        ClickBtn(BTN.NIVEL_GOBIERNO),
        Rows(["locales"]),
        ClickBtn(BTN.GOB_LOCALES_MANCOMUNIDADES),
        Rows(),
        ClickBtn(BTN.DEPARTAMENTO),
    ]
    slc = MEFScraper(stp2)
    print(slc.steps)
    r = slc.run(2020)
    print(r.result)
