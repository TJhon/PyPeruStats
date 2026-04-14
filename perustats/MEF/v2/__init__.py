from perustats.MEF.v2.constants import buttons as BTN
from perustats.MEF.v2.steps.click import ClickBtn, Rows

from .scrapper import MEFScraper

if __name__ == "__main__":
    from rich import print

    stp1 = [
        Rows(["total"]),
        ClickBtn(BTN.NIVEL_GOBIERNO),
        Rows(["locales"]),
        ClickBtn(BTN.GOB_LOCALES_MANCOMUNIDADES),
    ]
    r = MEFScraper(stp1, convert_numeric=False).run(2020)
    # print(r.config)
    # s = r.initial_session
    # print(s)

    # print(r.steps)
