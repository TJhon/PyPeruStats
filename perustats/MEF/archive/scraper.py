"""
Scraper unificado para datos de SIAF MEF (Ingresos y Gastos)
"""

from pathlib import Path
from typing import List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

from perustats.MEF.step import SearchTextStep, Step

from .constants import COLORS_PROGRESS, get_config
from .utils import (
    build_payload,
    build_search_payload,
    extract_states,
    filename_save,
    find_row_by_text,
    get_console,
    get_grp_from_row,
    has_search_panel,
    html_table_to_dataframe,
    post_info,
    save_dataframe,
)

console = get_console()


class MEFScraper:
    """
    Scraper unificado para extraer datos del SIAF MEF (Sistema Integrado de Administración Financiera)

    Soporta:
    - Ingresos: años 2009-2026
    - Gastos: años 2009-2026

    Uso:
        # Para ingresos
        scraper = MEFScraper(tipo='ingreso', master_dir_save='./data/raw/ingresos/')
        scraper.run(year=2010, steps=STEPS_INGRESO_2009_2011)

        # Para gastos
        scraper = MEFScraper(tipo='gasto', master_dir_save='./data/raw/gastos/')
        scraper.run(year=2010, steps=STEPS_GASTO_2009_2011)
    """

    def __init__(self, tipo: str = "gasto", master_dir_save: str = "./data/raw"):
        """
        Inicializa el scraper

        Args:
            tipo: "gasto" o "ingreso"
            master_dir_save: Directorio raíz donde guardar los datos
        """
        if tipo not in ["gasto", "ingreso"]:
            raise ValueError(f"Tipo '{tipo}' no válido. Use 'gasto' o 'ingreso'")

        self.tipo = tipo
        self.master_dir_save = Path(master_dir_save)
        self.master_dir_save.mkdir(parents=True, exist_ok=True)

        # Configuración que se establecerá al ejecutar run()
        self.year = None
        self.config = None
        self.session = None
        self.url = None
        self.cols = None
        self.buttons = None
        self.button_labels = None
        self.save_dir = None
        self.colors = COLORS_PROGRESS

    def _setup_year(self, year: int, act_proy="ActProy"):
        """
        Configura los parámetros específicos del año

        Args:
            year: Año a procesar
            act_proy: solo aplicable para gasto, todo (ActProy), Actividades, Proyectos. parametro irrelevantes si es para ingresos
        """
        self.year = year
        self.config = get_config(year, self.tipo)
        self.act_proy = act_proy
        if self.tipo == "gasto":
            if act_proy not in ["ActProy", "Actividad", "Proyecto"]:
                raise ValueError(
                    "Para `gasto` solo esta disponible: ActProy [default], Actividad, Proyecto"
                )
            self.url = self.config["url"].format(year=year, ap=act_proy)
        else:
            self.url = self.config["url"].format(year=year)

        self.cols = self.config["columns"]
        self.buttons = self.config["buttons"]
        # console.print(self.buttons)
        self.button_labels = self.config["button_labels"]

        # Directorio específico del año
        self.save_dir = self.master_dir_save / str(year)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
        console.print(
            f"[bold cyan]  Configuración para {self.tipo.upper()} - Año {year}[/bold cyan]"
        )
        console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
        console.print(f"  URL: {self.url}")

        console.print(f"  Directorio de guardado: {self.save_dir}\n")

    def _init_session(self) -> tuple:
        """
        Inicializa la sesión HTTP y obtiene el estado inicial

        Returns:
            Tupla (estados_iniciales, dataframe_inicial)
        """
        self.session = requests.Session()
        response = self.session.get(self.url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        initial_states = extract_states(soup)
        initial_df = html_table_to_dataframe(soup, columns=self.cols, convert=False)

        return initial_states, initial_df, soup

    def _execute_post_steps(
        self,
        soup: BeautifulSoup,
        state: dict,
        df: pd.DataFrame,
        post_step: SearchTextStep,
        step_idx: int,
    ) -> tuple:
        """
        Ejecuta los substeps de búsqueda (por código o descripción)

        Args:
            soup: BeautifulSoup del HTML actual
            state: Estado actual (ViewState, EventValidation)
            df: DataFrame actual (puede ser ignorado si hay substeps)
            substeps: Lista de substeps a ejecutar
            step_idx: Índice del paso principal (para colores)

        Returns:
            Tupla (nuevo_soup, nuevos_estados, nuevo_df, grp_seleccionado)
        """
        color = self.colors[step_idx % len(self.colors)]
        step_spaces = "  " * (step_idx + 2)  # Extra indentación para substeps

        current_soup = soup
        current_state = state
        current_df = df

        # for substep_idx, substep in enumerate(substeps):
        search_query = post_step.query
        search_type = post_step.search_type
        select_row_text = post_step.select_row_text
        console.print(
            f"[gray]{step_spaces} Buscando '{search_query}' usando el buscador de la plataforma del MEF<:40",
            end="\r",
        )
        # Verificar que el panel de búsqueda existe
        if not has_search_panel(current_soup):
            console.print(
                f"[red]{step_spaces}ADVERTENCIA: Panel de búsqueda no encontrado para este paso, probando sin paneles"
            )
            return state, df, soup

        # Construir payload de búsqueda
        search_payload = build_search_payload(
            current_soup,
            self.year,
            current_state,
            search_query,
            search_type,
            tipo=self.tipo,
            act_proy=self.act_proy,
        )

        # Ejecutar búsqueda
        try:
            new_states, new_df, new_soup = post_info(
                self.session, self.url, search_payload, self.cols, updated=True
            )

        except Exception as e:
            console.print(f"[red]{step_spaces}❌ Error en búsqueda: {e}[/red]")
            raise

        console.print(
            f"[green]{step_spaces}   Filas encontradas {len(new_df)} resultados[/green]",
            end="\r",
        )

        # Si hay select_row_text, buscar esa fila específica
        if select_row_text:
            try:
                idx = find_row_by_text(new_df, select_row_text)
                # print(new_df)
                new_df = new_df.iloc[[idx]]
                # print(new_df)
                selected_value = new_df[self.cols[1]][0]
                console.print(
                    f"[green]{step_spaces}   ✓ Seleccionado: {selected_value}[/green]",
                    end="\r",
                )
            except ValueError:
                console.print(
                    f"[red]{step_spaces}   ❌ No se encontró '{select_row_text}' en resultados[/red]"
                )
                raise

        # Actualizar estados para el siguiente substep
        current_soup = new_soup
        current_state = new_states
        current_df = new_df

        return current_soup, current_state, current_df

    def _process_from_step(
        self,
        soup,
        step_idx: int,
        state: dict,
        df: pd.DataFrame,
        metadata: dict,
        steps: List[Step],
    ) -> List[pd.DataFrame]:
        """
        Procesa recursivamente desde un paso específico

        Args:
            step_idx: Índice del paso actual
            state: Estado actual (ViewState, EventValidation)
            df: DataFrame actual
            metadata: Metadatos acumulados
            steps: Lista de pasos a ejecutar

        Returns:
            Lista de DataFrames con los resultados
        """

        n_steps = len(steps)

        # Caso base: ya procesamos todos los pasos
        if step_idx >= n_steps:
            return []

        step_config = steps[step_idx]
        color = self.colors[step_idx % len(self.colors)]
        is_final = step_idx + 1 == n_steps
        should_save = step_config.save_group
        click_bttn = step_config.click_bttn
        name_col = step_config.name
        step_description = step_config.desc or f"Paso {step_idx + 1}"
        text_search = step_config.select_row_text
        extras_params = step_config.extras or {}
        post_step = step_config.post_step
        should_loop = text_search is None

        step_spaces = "  " * (step_idx + 1)

        if name_col is not None:
            step_description = name_col

        if not is_final:
            msg = (
                f"[{color}]: {step_spaces} Step {step_idx + 1}: {step_description:<40}"
            )
            console.print(msg)

        # ========================================
        # CASO 1: Paso sin loop (selección única)
        # ========================================

        if not should_loop:
            idx = find_row_by_text(df, text_search)
            grp = df.iloc[idx][self.cols[0]]

            if name_col is not None:
                metadata[name_col] = [df.iloc[idx][self.cols[1]]]

            payload = build_payload(
                soup,
                self.year,
                state,
                click_bttn,
                grp,
                self.buttons,
                self.button_labels,
                extras=extras_params,
                tipo=self.tipo,
                act_proy=self.act_proy,
            )
            new_states, new_df, new_soup = post_info(
                self.session, self.url, payload, self.cols
            )
            if post_step:
                # todo: implmentar esto
                # despues de hacer el previo post buscaremos con la bsuqueda
                # ejecuta un post y devuelve un nuevo html con el df nuevo y stados nuevos

                new_soup, new_states, new_df = self._execute_post_steps(
                    new_soup, new_states, new_df, post_step, step_idx
                )

            return self._process_from_step(
                new_soup, step_idx + 1, new_states, new_df, metadata.copy(), steps
            )

        # ========================================
        # CASO 2: Paso con loop (itera todas las filas)
        # ========================================
        all_data = []
        total_rows = len(df)

        for i, row in df.iterrows():
            grp = get_grp_from_row(df, i)
            current_meta = metadata.copy()
            current_value = df.iloc[i][self.cols[1]]

            if name_col is not None:
                current_meta[name_col] = [current_value]

            # Checkpoint: verificar si el archivo ya existe
            if should_save and name_col is not None:
                path = filename_save(
                    name=name_col, value=current_value, save_dir=self.save_dir
                )
                if path.exists():
                    console.print(
                        f"[yellow]{step_spaces} Skip {name_col}: {current_value} (ya existe)[/yellow]"
                    )
                    continue

            # Mostrar progreso
            end = "\r" if is_final else "\n"
            console.print(
                f"[{color}]{step_spaces}{'  '}-> [{i + 1}/{total_rows}] {name_col}: {current_value:<40}",
                end=end,
            )

            # Hacer POST
            payload = build_payload(
                soup,
                self.year,
                state,
                click_bttn,
                grp,
                self.buttons,
                self.button_labels,
                tipo=self.tipo,
                act_proy=self.act_proy,
            )

            try:
                new_states, new_df, new_soup = post_info(
                    self.session, self.url, payload, self.cols
                )
            except Exception as e:
                console.print(f"[red]{step_spaces}Error en POST: {e}[/red]")
                continue

            # Paso final: agregar metadata y guardar
            if is_final:
                meta_df = pd.DataFrame(current_meta)
                new_df = new_df.assign(**meta_df.iloc[0].to_dict())
                all_data.append(new_df)
            else:
                # Recursión: continuar al siguiente paso
                child_results = self._process_from_step(
                    new_soup, step_idx + 1, new_states, new_df, current_meta, steps
                )
                all_data.extend(child_results)

            # Guardar incrementalmente si está configurado
            if should_save and name_col is not None and all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                save_dataframe(combined_df, self.save_dir, name_col, current_value)
                all_data = []  # Resetear para el siguiente grupo

        return all_data

    def run(
        self, year: int, steps: List[Step], act_proy="ActProy"
    ) -> Optional[pd.DataFrame]:
        """
        Ejecuta el scraping para un año específico con los pasos definidos

        Args:
            year: Año a procesar
            steps: Lista de diccionarios con la configuración de cada paso
                   Estructura de cada paso:
                   {
                       "desc": "Descripción del paso",
                       "select_row_text": "texto" o None,  # None = loop sobre todas las filas
                       "click_bttn": "nombre_boton",
                       "name": "nombre_columna",  # opcional
                       "loop": True/False,  # opcional, redundante con select_row_text
                       "save_group": True/False,  # opcional, guardar incrementalmente
                   }
            act_proy: solo aplicable para "gasto", todo (ActProy), Actividades, Proyectos

        Returns:
            DataFrame con todos los resultados o None si se guardó incrementalmente

        Ejemplo de steps:
            STEPS = [
                dict(
                    desc="Seleccionar total, click nivel de gobierno",
                    select_row_text="total",
                    click_bttn="nivel_gobierno",
                ),
                dict(
                    desc="Seleccionar gob locales, click sub tipo",
                    select_row_text="locales",
                    click_bttn="sub_tipo_gobierno",
                ),
                dict(
                    name="funcion",
                    desc="Iterar todas las funciones, click departamento",
                    select_row_text=None,  # None = loop
                    click_bttn="departamento",
                    save_group=True,
                ),
                dict(
                    name="departamento",
                    desc="Iterar todos los departamentos, click municipalidad",
                    select_row_text=None,
                    click_bttn="municipalidad",
                ),
            ]
        """
        # Configurar año
        self._setup_year(year, act_proy=act_proy)

        # Inicializar sesión
        console.print("[bold]Inicializando sesión...[/bold]", end="\r")
        initial_states, initial_df, initial_soup = self._init_session()

        # Ejecutar proceso recursivo
        console.print("[bold]Iniciando proceso de extracción...[/bold]", end="\r")
        results = self._process_from_step(
            soup=initial_soup,
            step_idx=0,
            state=initial_states,
            df=initial_df,
            metadata={"year": year},
            steps=steps,
        )

        # Consolidar resultados finales si no se guardaron incrementalmente
        if results:
            final_df = pd.concat(results, ignore_index=True)
            final_path = self.save_dir / f"{year}_completo.csv"
            final_df.to_csv(final_path, index=False)
            console.print("\n[bold green]✓ Proceso completado![/bold green]")
            console.print(f"  Archivo final: {final_path}")
            console.print(f"  Total de filas: {len(final_df)}")
            return final_df
        else:
            console.print("\n[bold green]✓ Proceso completado![/bold green]")
            console.print("  Datos guardados incrementalmente")
            return None
