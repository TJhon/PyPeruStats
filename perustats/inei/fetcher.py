"""
INEIFetcher: main entry-point for downloading INEI microdata.

Typical usage
-------------
>>> from perustats.inei import INEIFetcher
>>>
>>> fetcher = INEIFetcher(survey="enaho", years=range(2018, 2023))
>>> (fetcher
...     .fetch_modules()
...     .download(module_codes=[1, 13, 22])
...     .organize(organize_by="year"))
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Literal, Optional

import pandas as pd
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .constants import DEFAULT_FORMAT_PREFERENCE
from .downloader import Downloader
from .module_fetcher import ModuleFetcher
from .organizer import Organizer
from .surveys.registry import Survey, registry
from .utils.db_utils import DatabaseManager

console = Console()


class INEIFetcher:
    """
    High-level interface for downloading INEI microdata.

    Parameters
    ----------
    survey:
        Survey code registered in :data:`~perustats.inei.surveys.registry.registry`
        (e.g. ``'enaho'``, ``'endes'``, ``'enapres'``).
        Run ``registry.list_codes()`` to see all available codes.
    years:
        Iterable of years to fetch.
    master_directory : str, default="./data/"
        Root directory where all downloaded and processed files will be stored.
    inei_directory : str, default="microdatos_inei"
        Subdirectory inside *master_directory* used to organize INEI data.
    parallel_jobs:
        Number of concurrent download threads.
    preferred_formats:
        Ordered list of format preferences. The first format with a valid URL
        for a given module is used.
    sql_file:
        Path (relative to *master_directory*) for the SQLite progress database.
    """

    def __init__(
        self,
        survey: str,
        years: List[int],
        master_directory: str = "./data/",
        inei_directory: str = "microodatos_inei",
        parallel_jobs: int = 2,
        preferred_formats: List[Literal["stata", "spss", "csv", "dbf"]] = None,
        sql_file: Optional[str] = None,
    ) -> None:
        self.survey: Survey = registry.get(survey)
        self.years: List[int] = list(years)
        self.parallel_jobs = parallel_jobs
        self.preferred_formats = preferred_formats or DEFAULT_FORMAT_PREFERENCE

        # ── Directory layout ───────────────────────────────────────────
        root = Path(master_directory) / inei_directory / self.survey.code
        self._dirs = {
            "zips": root / "0_zips",
            "unzip": root / "1_unzipped",
            "organized": root / "2_organized",
        }
        for d in self._dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        # ── Database ───────────────────────────────────────────────────
        db_path = Path(master_directory) / (sql_file or "referrer.db")
        self.db = DatabaseManager(db_path)

        # ── Sub-components ─────────────────────────────────────────────
        self._module_fetcher = ModuleFetcher(self.survey)
        self._downloader = Downloader(self.db, parallel_jobs)

        # Populated by fetch_modules()
        self.modules_df: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------ #
    # Step 1 – fetch module listings                                       #
    # ------------------------------------------------------------------ #

    def fetch_modules(self) -> "INEIFetcher":
        """
        Retrieve (or load from cache) the module list for every requested year.

        Returns self for method chaining.
        """
        results: List[pd.DataFrame] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Fetching [yellow]{self.survey.code.upper()}[cyan] modules…",
                total=len(self.years),
            )
            for year in self.years:
                cached = self.db.get_cached_modules(
                    self.survey.code, year, self.survey.period
                )
                if cached is not None:
                    results.append(cached)
                else:
                    df = self._module_fetcher.fetch(year)
                    df["module_code"] = df["module_code"].astype(str).str.zfill(4)
                    df["url"] = (
                        df[list(self.preferred_formats)].bfill(axis=1).iloc[:, 0]
                    )
                    # Compute local paths
                    df["path_download"] = df.apply(
                        lambda r: str(
                            self._dirs["zips"]
                            / f"{r['year_ref']}_mod_{r['module_code']}.zip"
                        ),
                        axis=1,
                    )
                    df["path_extract"] = df.apply(
                        lambda r: str(
                            self._dirs["unzip"]
                            / f"{r['year_ref']}_mod_{r['module_code']}"
                        ),
                        axis=1,
                    )
                    self.db.insert_modules(df)
                    results.append(df)
                progress.update(task, advance=1)

        df = pd.concat(results, ignore_index=True).drop_duplicates()

        self.modules_df = df
        console.print(
            f"[green]✓ Found [bold]{len(df)}[/bold] modules for "
            f"[yellow]{self.survey.code.upper()}[/yellow]"
        )
        return self

    # ------------------------------------------------------------------ #
    # Step 2 – download + extract                                          #
    # ------------------------------------------------------------------ #

    def download(
        self,
        module_codes: Optional[List[int]] = None,
        force: bool = False,
        remove_zip_after_extract: bool = False,
    ) -> "INEIFetcher":
        """
        Download and extract ZIP files for the fetched modules.

        Parameters
        ----------
        module_codes:
            Restrict download to these module codes (all modules if omitted).
            Pass ``None`` or omit to download everything.
        force:
            Re-download even if a valid ZIP already exists.
        remove_zip_after_extract:
            Delete each ZIP after successful extraction.

        Returns self for method chaining.
        """
        self._require_modules()

        # Guard: reject anything that is not a real list/tuple of ints
        if module_codes is not None:
            if not isinstance(module_codes, (list, tuple, set)) or isinstance(
                module_codes, bool
            ):
                raise TypeError(
                    f"module_codes must be a list/tuple of integers or None, "
                    f"got {type(module_codes).__name__!r}. "
                    "To download all modules, pass module_codes=None or omit it."
                )
            module_codes = list(module_codes)

        df = self.modules_df.copy()
        df = df.dropna(subset=["url"])

        if module_codes:
            padded = [str(int(c)).zfill(4) for c in module_codes]
            df = df[df["module_code"].isin(padded)]

        rows = df.to_dict("records")
        self._downloader.download_and_extract(
            rows, force=force, remove_zip_after_extract=remove_zip_after_extract
        )
        return self

    # ------------------------------------------------------------------ #
    # Step 3 – organize                                                    #
    # ------------------------------------------------------------------ #

    def organize(
        self,
        organize_by: Literal["module", "year"] = "module",
        keep_original_names: bool = True,
        operation: Literal["move", "copy"] = "copy",
        deduplicate_docs_by_hash: bool = True,
    ) -> "INEIFetcher":
        """
        Organize extracted files into a clean directory structure.

        Returns self for method chaining.
        """
        self._require_modules()
        organizer = Organizer(
            organized_directory=self._dirs["organized"],
            unzipped_directory=self._dirs["unzip"],
            db=self.db,
            modules_df=self.modules_df,
        )
        organizer.organize(
            organize_by=organize_by,
            keep_original_names=keep_original_names,
            operation=operation,
            deduplicate_docs_by_hash=deduplicate_docs_by_hash,
        )
        return self

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _require_modules(self) -> None:
        if self.modules_df is None:
            raise RuntimeError("Call fetch_modules() before this step.")

    def __repr__(self) -> str:
        n = len(self.modules_df) if self.modules_df is not None else "?"
        return (
            f"INEIFetcher(survey={self.survey.code!r}, years={self.years}, modules={n})"
        )


if __name__ == "__main__":
    pass

    # from inei import INEIFetcher

    INEIFetcher("enaho", years=range(2018, 2020)).fetch_modules().download(
        module_codes=[1, 2, 5, 4]
    ).organize("year")
    INEIFetcher("renamu", years=range(2018, 2020)).fetch_modules().download().organize(
        "year"
    )

    INEIFetcher("enapres", years=range(2018, 2020)).fetch_modules().download().organize(
        "year"
    )

    INEIFetcher("endes", years=range(2018, 2020)).fetch_modules().download().organize(
        "year"
    )
    INEIFetcher(
        "enaho_panel", years=range(2018, 2020)
    ).fetch_modules().download().organize("year")
