from pathlib import Path
from typing import Literal

from rich import print

from perustats.MEF.v2.constants.config import Config, get_config
from perustats.MEF.v2.steps.click import Search
from perustats.MEF.v2.steps.workflow import Step, Workflow
from perustats.MEF.v2.utils.html import has_search_panel
from perustats.MEF.v2.utils.http import (
    build_payload,
    build_search_payload,
    init_session,
    post_info,
)
from perustats.MEF.v2.utils.parse_file import filename_save
from perustats.MEF.v2.utils.tables import filter_content, get_grp_from_row

print
post_info


class MEFScraper:
    def __init__(
        self,
        steps=[],
        tipo: Literal["gasto", "ingreso"] = "gasto",
        act_proy: Literal["ActProy", "Actividad", "Proyecto"] = "ActProy",
        master_dir_save: str = "./data/mef/",
        convert_numeric: bool = True,
    ):
        if tipo not in ["gasto", "ingreso"]:
            raise ValueError(f"Tipo '{tipo}' no válido. Use 'gasto' o 'ingreso'")

        wk = Workflow(steps)
        self.steps = wk.p_steps
        self.tipo = tipo
        self.master_dir_save = Path(master_dir_save)
        self.act_proy = act_proy
        self.convert_numeric = convert_numeric

        # Configuración que se establecerá al ejecutar run()
        self.config = None

        self.year = None
        self.session = None
        self.url = None
        self.cols = None
        self.buttons = None
        self.button_labels = None
        self.save_dir = None

    def _do_post(self, soup, state, grp, click_bttn, extras=None):
        payload = build_payload(
            soup=soup,
            year=self.year,
            state=state,
            button_key=click_bttn,
            grp=grp,
            extras=extras or {},
            tipo=self.tipo,
            act_proy=self.act_proy,
        )
        print(payload)

        return post_info(
            self.initial_session.session, self.config.url, payload, self.config.columns
        )

    def _already_saved(self, name_col, value):
        if name_col is None:
            return False
        path = filename_save(name=name_col, value=value, save_dir=self.save_dir)
        if path.exists():
            return True
        return False

    def run(self, year: int) -> "MEFScraper":
        self._setup_year(year=year)

        initial_config = self.initial_session
        initial_states = initial_config.states
        soup = initial_config.soup
        df = initial_config.df
        # session = initial_config.session
        result = self._process_steps(
            soup=soup, step_idx=0, state=initial_states, df=df, metadata={"year": year}
        )
        self.result = result
        return self

    def _execute_search_step(self, soup, state, df, post_step: Search):
        """ejecuta esto cuando tengo un Step y Search diferente a None"""
        if not has_search_panel(soup):
            return state, df, soup  # <-- ojo: orden distinto al original*

        search_payload = build_search_payload(
            soup,
            year=self.year,
            state=state,
            search_query=post_step.query,
            search_type=post_step.method,
            tipo=self.tipo,
            act_proy=self.act_proy,
        )
        try:
            new_states, new_df, new_soup = post_info(
                self.session, self.url, search_payload, self.cols, updated=True
            )
        except Exception:
            raise

        return new_soup, new_states, new_df

    def _process_steps(self, soup, step_idx, state, df, metadata):

        steps = self.steps

        step: Step = steps[step_idx]
        print(step)
        is_final = step_idx + 1 == len(steps)

        df = filter_content(df, step.rows.rows)

        result_data = []

        for i, _ in df.iterrows():
            grp_row = get_grp_from_row(df, i)
            result = self._do_post(soup, state, grp_row, step.click.button)
            if is_final:
                result_data.append(result.df)

        if is_final:
            print(result_data)
            return

        self._process_steps(soup, step_idx + 1, state, df, metadata)
        # # name_col = "step.name"
        # name_col = random.randint(1, 10)
        # name_col = f"c_{name_col}"

        # rows = step.rows.rows
        # button_id = step.click.button

        # df = filter_content(df, rows=rows)

        # all_data = []

        # for i, _ in df.iterrows():
        #     current_value = df.iloc[i][self.config.columns[1]]
        #     current_meta = update_meta(metadata.copy(), i)

        #     # todo: aqui modificar el nombre
        #     if step.save and self._already_saved(name_col, current_value):
        #         continue
        #     try:
        #         new_states, new_df, new_soup = self._do_post(
        #             soup, state, get_grp_from_row(df, i), button_id
        #         )
        #     except Exception:
        #         continue

        #     if is_final:
        #         new_df = new_df.assign(**pd.DataFrame(current_meta).iloc[0].to_dict())
        #         all_data.append(new_df)
        #     else:
        #         all_data.extend(recurse(new_soup, new_states, new_df, current_meta))

        # return all_data

    def _setup_year(
        self,
        year: int,
    ):
        config = get_config(year, self.tipo)

        act_proy = self.act_proy

        if self.tipo == "gasto":
            if act_proy not in ["ActProy", "Actividad", "Proyecto"]:
                raise ValueError(
                    "Para `gasto` solo esta disponible: ActProy [default], Actividad, Proyecto"
                )
            url = config.url.format(year=year, ap=act_proy)
        else:
            url = config.url.format(year=year)

        initial_session = init_session(url, config.columns, self.convert_numeric)
        # obtenermos la primera visita a la pagina en el anio n
        self.initial_session = initial_session
        # obtnemos la metadata configurada para ese anio
        self.config = Config(range(1, 2), url, config.columns)
        # Directorio específico del año
        self.save_dir = self.master_dir_save / self.tipo / str(year)
        self.save_dir.mkdir(parents=True, exist_ok=True)
