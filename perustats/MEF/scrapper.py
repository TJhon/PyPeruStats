from pathlib import Path
from typing import List, Literal

import pandas as pd
from rich import print

from perustats.MEF.constants.config import Config, get_config
from perustats.MEF.steps.click import Search
from perustats.MEF.steps.workflow import Workflow
from perustats.MEF.utils.html import STATESHTML, has_search_panel
from perustats.MEF.utils.http import (
    build_payload,
    build_search_payload,
    init_session,
    post_info,
)
from perustats.MEF.utils.parse_file import filename_save
from perustats.MEF.utils.tables import filter_content

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

    def _do_post(self, soup, state: STATESHTML, grp, click_bttn, extras=None):
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
        # print(payload)

        result = post_info(
            self.initial_session.session, self.config.url, payload, self.config.columns
        )
        # print(result.df)
        return result

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
        result = self._proces_step(
            step_idx=0,
            df=df,
            state=initial_states,
            soup=soup,
            metadata={"year": [year]},
        )
        self.result = pd.concat(result)

        return self

    def _execute_search_step(self, soup, state, df, post_step: Search):
        """ejecuta esto cuando tengo un Step y Search diferente a None"""
        if not has_search_panel(soup):
            return soup, state, df

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
            result = post_info(
                self.initial_session.session,
                self.config.url,
                search_payload,
                self.config.columns,
            )
            new_soup = result.soup
            new_states = result.states
            new_df = result.df
        except Exception:
            raise

        return new_soup, new_states, new_df

    def _proces_step(
        self,
        soup,
        step_idx: int,
        state: STATESHTML,
        df: pd.DataFrame,
        metadata: dict,
    ) -> List[pd.DataFrame]:

        steps = self.steps
        is_final = step_idx + 1 == len(steps)
        columns = self.config.columns

        if step_idx >= len(steps):
            return []

        step = steps[step_idx]

        name_col = None

        as_col = step.click.as_column
        if as_col and step_idx >= 1:
            name_col = steps[step_idx - 1].click.name

        click_bttn = step.click.button
        text_search = step.rows.rows

        should_save = step.save is not None
        post_step = step.search

        extras_params = {}

        # print(step)
        df_filtered = filter_content(df, text_search)
        results = []

        for i, row in df_filtered.iterrows():
            grp = row.get(columns[0])
            current_meta = metadata.copy()
            current_value = row.get(columns[1])

            if name_col:
                current_meta[name_col] = [current_value]

            result_post = self._do_post(
                soup=soup,
                state=state,
                grp=grp,
                click_bttn=click_bttn,
                extras=extras_params,
            )
            child_df = result_post.df
            child_soup = result_post.soup
            child_states = result_post.states

            if post_step is not None:
                child_soup, child_states, child_df = self._execute_search_step(
                    child_soup, child_states, child_df, post_step
                )

            if is_final:
                last_name = step.click.name
                meta_df = pd.DataFrame(current_meta)
                child_df = (
                    child_df.assign(**meta_df.iloc[0].to_dict())
                    .drop(columns=[columns[0]])
                    .rename(columns={columns[1]: last_name})
                )

                results.append(child_df)
            else:
                child = self._proces_step(
                    soup=child_soup,
                    step_idx=step_idx + 1,
                    state=child_states,
                    df=child_df,
                    metadata=current_meta,
                )
                results.extend(child)
        return results

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
        self.year = year
        # Directorio específico del año
        self.save_dir = self.master_dir_save / self.tipo / str(year)
        self.save_dir.mkdir(parents=True, exist_ok=True)
