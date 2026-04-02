"""
Main fetcher class for downloading INEI microdatos.
"""

import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from typing import List, Literal

import pandas as pd
import requests
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from .constants import CACHE_MICRODATOS, RELEVANT_EXTENSIONS
from .utils import (
    _file_hash,
    create_environment,
    get_modules_details,
    is_zip_valid,
    slugify,
)

console = Console()


class MicrodatosINEIFetcher:
    """
    Fetcher for downloading and organizing INEI microdatos (microdata) .

    This class handles:
    - Fetching available modules from INEI
    - Downloading data files in multiple formats
    - Organizing files by year or module
    - Extracting and managing ZIP archives
    """

    def __init__(
        self,
        survey: Literal["enaho", "endes", "enapres", "renamu"],
        years: List[int],
        period="anual",
        master_directory: str = "./microdatos_inei",
        parallel_jobs: int = 2,
        sql_file: str = None,
        prefered_order_formats: Literal["stata", "spss", "csv", "dbf"] = [
            "stata",
            "spss",
            "csv",
            "dbf",
        ],
    ):
        """
        Initialize the INEI microdatos fetcher.

        Args:
            survey: Survey type to fetch (enaho, endes, or enapres)
            years: List of years to fetch data for
            master_directory: Root directory for storing downloaded data
            parallel_jobs: Number of parallel jobs for downloads
        """
        self.survey = survey
        self.years = years
        self.dirs, self.conn = create_environment(survey, master_directory, sql_file)
        self.period = period
        self.formats = prefered_order_formats

        self.parallel_jobs = parallel_jobs
        self.zip_maps = []

    def _fetch_detail(self, year):
        """
        Extrae la tabla de modulos para ese anio, consultando la cache primero
        """
        df = get_modules_details(self.survey, year, self.period)
        return df

    def fetch_all_modules(self):
        """
        Fetch available modules for all specified years.

        Returns:
            Self for method chaining
        """

        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Fetching [yellow]{self.survey.upper()} [cyan]modules...",
                total=len(self.years),
            )
            for year in self.years:
                results.append(self._fetch_detail(year))
                progress.update(task, advance=1)

        df = pd.concat(results, ignore_index=True).drop_duplicates()
        # rutas de descarga
        df["module_code"] = df["module_code"].astype(str).str.zfill(4)
        df["url"] = df[self.formats].bfill(axis=1).iloc[:, 0]
        df["path_download"] = df.apply(
            lambda row: (
                self.dirs.get("zips")
                / f"{row['year_ref']}_mod_{row['module_code']}.zip"
            ),
            axis=1,
        )
        df["path_extract"] = df.apply(
            lambda row: (
                self.dirs.get("unzip") / f"{row['year_ref']}_mod_{row['module_code']}"
            ),
            axis=1,
        )
        self.modules_dataframe = df
        df.to_sql(CACHE_MICRODATOS, con=self.conn, index=False)
        return self

    def _download_single(self, row: dict) -> bool:
        url = row["url"]
        zip_path = row["path_download"]

        try:
            cmd = [
                "curl",
                "-s",
                "-L",
                url,
                "-o",
                str(zip_path),
                "-H",
                "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "-H",
                "Accept-Language: es,en;q=0.9",
                "-H",
                "Connection: keep-alive",
            ]
            subprocess.run(cmd, check=True)

        except Exception:
            return False

        # validar zip
        if not is_zip_valid(zip_path):
            try:
                os.remove(zip_path)
            except FileNotFoundError:
                pass

            try:
                # segundo intento usando
                r = requests.get(url, stream=True, timeout=60)
                r.raise_for_status()

                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)

            except Exception:
                return False

            if not is_zip_valid(zip_path):
                try:
                    os.remove(zip_path)
                except FileNotFoundError:
                    pass
                return False

        return True

    def download_zips(
        self,
        module_codes: List[int] = [],
        remove_zip_after_extract: bool = False,
        force_download: bool = True,
    ) -> "MicrodatosINEIFetcher":
        """
        Download ZIP files for specified modules.

        Args:
            formats: List of formats to download (stata, spss, csv, dbf)
            force_download: Force re-download even if file exists
            module_codes: List of module codes to download (empty = all)
            remove_zip_after_extract: Delete ZIP files after extraction

        Returns:
            Self for method chaining
        """

        # Filter by module codes if specified
        filtered_modules = [str(x).zfill(4) for x in module_codes]
        df = self.modules_dataframe.copy()

        if filtered_modules:
            df = df.query("module_code in @filtered_modules")

        for _, row in df.iterrows():
            r = self._download_single(row)
            if r:
                # update la columna del sql downloaded a true para el row[url]
                # extraer
                status = self._extract_zips(row, remove_zip_after_extract)
                # actualiar ell extracted y deleted en el sql
                pass

        return self

    def _extract_zips(self, row: dict, remove_after: bool = False) -> None:
        """
        Extract downloaded ZIP files.

        Args:
            remove_after: Delete ZIP files after extraction
        """
        zip_local = Path(row.get("path_download"))
        zip_destination = Path(row.get("path_extract"))
        extracted = False
        deleted = False
        if zip_local.exists():
            if zip_destination.exists():
                zip_destination.unlink()
            with zipfile.ZipFile(zip_local, "r") as zip_file:
                zip_file.extractall(zip_destination)
                extracted = True
                if remove_after:
                    zip_local.unlink()
                    deleted = True
        return dict(extrated=extracted, deleted=deleted)

    def organize_files(
        self,
        organize_by: Literal["module", "year"] = "module",
        keep_original_names: bool = True,
        operation: Literal["move", "copy"] = "copy",
        docs_by_hash: bool = True,
    ) -> "MicrodatosINEIFetcher":
        """
        Organize extracted files by module or year.

        Args:
            organize_by: Organization scheme (module or year)
            keep_original_names: Keep original filenames
            operation: Move or copy files
            docs_by_hash: Move or copy documentation omitiendo archivos duplicados usando el hash del archivo

        Returns:
            Self for method chaining
        """
        os.makedirs(self.organized_directory, exist_ok=True)
        operation_fn = shutil.move if operation == "move" else shutil.copy2

        files_by_destination = {}

        # Collect data files
        for root, _, files in os.walk(self.unzipped_directory):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in RELEVANT_EXTENSIONS:
                    continue

                full_path = Path(root) / file
                relative_parts = Path(root).relative_to(self.unzipped_directory).parts
                if not relative_parts:
                    continue

                year_module = relative_parts[0]  # e.g., "2014_mod_001"
                parts = year_module.split("_mod_")
                if len(parts) != 2:
                    continue
                year, module_code = parts[0], parts[1]

                # Get module name
                module_row = self.modules_dataframe[
                    (self.modules_dataframe["year"] == int(year))
                    & (
                        self.modules_dataframe["module_code"].astype(str).str.zfill(3)
                        == module_code
                    )
                ]
                module_name = (
                    module_row["module_name"].iloc[0]
                    if not module_row.empty
                    else "Unknown"
                )
                normalized_module = slugify(module_name)

                # Determine destination folder
                if organize_by == "module":
                    folder = (
                        self.organized_directory
                        / "by_module"
                        / f"{module_code}_{normalized_module}"
                    )
                else:
                    folder = self.organized_directory / "by_year" / year

                # Determine new filename
                if keep_original_names:
                    base_name = file
                    if organize_by == "module":
                        new_name = f"{year}_{base_name}"
                    else:
                        new_name = f"{module_code}_{base_name}"
                else:
                    base_name = file
                    new_name = base_name

                key = str(folder)
                if key not in files_by_destination:
                    files_by_destination[key] = []

                files_by_destination[key].append(
                    {
                        "source": full_path,
                        "destination_folder": folder,
                        "original_name": base_name,
                        "new_name_base": new_name,
                        "size": full_path.stat().st_size,
                    }
                )

        # Process files by destination

        for folder_key, file_list in files_by_destination.items():
            folder = Path(folder_key)
            os.makedirs(folder, exist_ok=True)

            if not keep_original_names:
                # Sort by size (largest first)
                file_list.sort(key=lambda x: x["size"], reverse=True)
                for idx, file_info in enumerate(file_list, start=1):
                    name_parts = file_info["new_name_base"].rsplit(".", 1)
                    if len(name_parts) == 2:
                        base, ext = name_parts
                        final_name = f"{base}_{idx}.{ext}"
                    else:
                        final_name = f"{file_info['new_name_base']}_{idx}"
                    destination = folder / final_name
                    operation_fn(file_info["source"], destination)

            else:
                # Keep original names, handle collisions
                name_count = {}
                for file_info in file_list:
                    name = file_info["new_name_base"]
                    if name in name_count:
                        name_count[name] += 1
                        name_parts = name.rsplit(".", 1)
                        if len(name_parts) == 2:
                            base, ext = name_parts
                            new_name = f"{base}_{name_count[name]}.{ext}"
                        else:
                            new_name = f"{name}_{name_count[name]}"
                    else:
                        name_count[name] = 0
                        new_name = name
                    destination = folder / new_name.lower()
                    operation_fn(file_info["source"], destination)

        # Organize documentation (PDFs)
        self._organize_documentation(operation_fn, filter_hash=docs_by_hash)

        console.print(
            f"[green] Files organized in: "
            f"[blue]{self.organized_directory / f'by_{organize_by}'}"
        )
        return self

    def _organize_documentation(self, operation_fn, filter_hash: bool = True):
        """
        Organize PDF documentation files.

        Args:
            operation_fn: Function to use for moving/copying files
            filter_hash: If True, avoid duplicating identical PDFs (by content hash)
                        and keep a dictionary mapping canonical names to aliases.
        """
        pdf_directory = self.organized_directory / "documentation"
        os.makedirs(pdf_directory, exist_ok=True)

        # For old behavior (name + size) OR new behavior (hash)
        seen_keys = {}

        duplicates_map = {}
        if filter_hash:
            for file in pdf_directory.glob("*.pdf"):
                key = _file_hash(file)
                seen_keys[key] = file.name
                duplicates_map.setdefault(file.name, []).append(file.name)
        for root, _, files in os.walk(self.unzipped_directory):
            for file in files:
                if not file.lower().endswith(".pdf"):
                    continue

                source = Path(root) / file
                basename = file
                size = source.stat().st_size

                if filter_hash:
                    key = _file_hash(source)
                else:
                    key = (basename.lower(), size)

                if key in seen_keys:
                    canonical = seen_keys[key]
                    duplicates_map.setdefault(canonical, []).append(file)
                    continue

                # First time we see this document
                parent_name = source.parent.name
                final_pdf_name = slugify(file)
                if parent_name not in file:
                    final_pdf_name = f"{parent_name}_{file}"

                destination = pdf_directory / final_pdf_name

                # Handle file-name collisions safely
                counter = 1
                original_dest = destination
                while destination.exists():
                    base, *ext = original_dest.name.rsplit(".", 1)
                    if ext:
                        destination = pdf_directory / f"{base}_{counter}.{ext[0]}"
                    else:
                        destination = pdf_directory / f"{original_dest.name}_{counter}"
                    counter += 1

                operation_fn(source, destination)

                seen_keys[key] = destination.name
                duplicates_map.setdefault(destination.name, []).append(file)
        self.documentation_map = duplicates_map


if __name__ == "__main__":
    import time

    # # Ejemplo: ENDES 2011-2013
    inicio = time.time()
    endes = MicrodatosINEIFetcher(
        survey="endes",
        years=list(range(1990, 2024)),
        master_directory="./datos_inei",
        parallel_jobs=6,
    )
    mod_endes = endes.fetch_modules()

    mod_endes.download_zips(
        formats=["spss", "dbf", "stata", "csv"], module_codes=[64, 65, 73, 74]
    )

    mod_endes.organize_files(
        organize_by="year", keep_original_names=True, operation="copy"
    )
    mod_endes.organize_files(
        organize_by="module", keep_original_names=True, operation="copy"
    )

    # Ejemplo: ENAHO
    inei = MicrodatosINEIFetcher(
        survey="enaho",
        years=list(range(2000, 2025)),
        master_directory="./datos_inei",
        parallel_jobs=2,
    )
    mod_inei = inei.fetch_modules()

    mod_inei.download_zips(
        formats=["csv", "stata", "spss", "dbf"], module_codes=[1, 13, 22, 34]
    )

    mod_inei.organize_files(
        organize_by="year", keep_original_names=True, operation="copy"
    )
    mod_inei.organize_files(
        organize_by="module", keep_original_names=True, operation="copy"
    )
    # Ejemplo: ENAPRES
    enapres = MicrodatosINEIFetcher(
        survey="enapres",
        years=list(range(2000, 2025)),
        master_directory="./datos_inei",
        parallel_jobs=2,
    )
    mod_enapres = enapres.fetch_modules()

    mod_enapres.download_zips(
        formats=["stata", "csv", "spss", "dbf"], module_codes=[101, 102, 111]
    )

    mod_enapres.organize_files(
        organize_by="year", keep_original_names=True, operation="copy"
    )
    mod_enapres.organize_files(
        organize_by="module", keep_original_names=True, operation="copy"
    )
