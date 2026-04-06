"""
Organizer: moves or copies extracted data files into a clean directory
structure (by module or by year) and deduplicates documentation files.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, List, Literal

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

from .constants import DOC_EXTENSIONS, RELEVANT_EXTENSIONS
from .utils.db_utils import DatabaseManager
from .utils.file_utils import file_hash, slugify

console = Console()


class Organizer:
    """
    Organizes extracted microdata files into a structured output directory.

    Parameters
    ----------
    organized_directory:
        Root directory where organized files will be placed.
    unzipped_directory:
        Source directory containing the raw extracted module folders.
    db:
        Database manager used to record per-file ``organized`` progress.
    modules_df:
        DataFrame of module metadata (used to resolve module names).
    """

    def __init__(
        self,
        organized_directory: Path,
        unzipped_directory: Path,
        db: DatabaseManager,
        modules_df: pd.DataFrame,
    ) -> None:
        self.organized_dir = organized_directory
        self.unzipped_dir = unzipped_directory
        self.db = db
        self.modules_df = modules_df

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def organize(
        self,
        organize_by: Literal["module", "year"] = "module",
        keep_original_names: bool = True,
        operation: Literal["move", "copy"] = "copy",
        deduplicate_docs_by_hash: bool = True,
    ) -> None:
        """
        Organize data files from *unzipped_directory* into *organized_directory*.

        Parameters
        ----------
        organize_by:
            Whether to group files under ``by_module/`` or ``by_year/``.
        keep_original_names:
            If ``False``, files are renamed with a size-based numeric suffix to
            avoid collisions. If ``True``, original filenames are kept (with a
            counter suffix only when there are genuine collisions).
        operation:
            ``'copy'`` leaves originals untouched; ``'move'`` removes them.
        deduplicate_docs_by_hash:
            When ``True``, identical documentation files (same SHA-256) are
            stored only once in ``documentation/``.
        """
        op_fn = shutil.move if operation == "move" else shutil.copy2
        self._organize_data_files(organize_by, keep_original_names, op_fn)
        self._organize_documentation(op_fn, deduplicate_docs_by_hash)
        console.print(
            f"[green]Files organized under [blue]{self.organized_dir / f'by_{organize_by}'}"
        )

    # ------------------------------------------------------------------ #
    # Data files                                                           #
    # ------------------------------------------------------------------ #

    def _organize_data_files(
        self,
        organize_by: str,
        keep_original_names: bool,
        op_fn,
    ) -> None:
        files_by_dest: Dict[str, List[dict]] = {}

        for root, _, files in os.walk(self.unzipped_dir):
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext not in RELEVANT_EXTENSIONS:
                    continue

                full_path = Path(root) / fname
                relative_parts = Path(root).relative_to(self.unzipped_dir).parts
                if not relative_parts:
                    continue

                year_module = relative_parts[0]  # e.g. "2014_mod_0001"
                parts = year_module.split("_mod_")
                if len(parts) != 2:
                    continue
                year, module_code = parts[0], parts[1]

                module_name = self._resolve_module_name(year, module_code)

                if organize_by == "module":
                    folder = (
                        self.organized_dir
                        / "by_module"
                        / f"{module_code}_{slugify(module_name)}"
                    )
                    new_name = f"{year}_{fname}" if keep_original_names else fname
                else:
                    folder = self.organized_dir / "by_year" / year
                    new_name = (
                        f"{module_code}_{fname}" if keep_original_names else fname
                    )

                key = str(folder)
                files_by_dest.setdefault(key, []).append(
                    {
                        "source": full_path,
                        "folder": folder,
                        "new_name": new_name,
                        "size": full_path.stat().st_size,
                        "url": None,  # filled below if available
                    }
                )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Sorting modules ... ", total=len(files_by_dest)
            )

            for folder_key, file_list in files_by_dest.items():
                folder = Path(folder_key)
                folder.mkdir(parents=True, exist_ok=True)

                if not keep_original_names:
                    file_list.sort(key=lambda x: x["size"], reverse=True)
                    for idx, fi in enumerate(file_list, start=1):
                        stem, _, suf = fi["new_name"].rpartition(".")
                        final = (
                            f"{stem}_{idx}.{suf}" if suf else f"{fi['new_name']}_{idx}"
                        )
                        dest = folder / final
                        op_fn(fi["source"], dest)
                        self.db.mark_organized("", str(dest))  # url not available here
                else:
                    name_count: Dict[str, int] = {}
                    for fi in file_list:
                        name = fi["new_name"].lower()
                        if name in name_count:
                            name_count[name] += 1
                            stem, _, suf = name.rpartition(".")
                            final = (
                                f"{stem}_{name_count[name]}.{suf}"
                                if suf
                                else f"{name}_{name_count[name]}"
                            )
                        else:
                            name_count[name] = 0
                            final = name
                        dest = folder / final
                        op_fn(fi["source"], dest)
                        self.db.mark_organized("", str(dest))
                progress.update(task, advance=1)

    # ------------------------------------------------------------------ #
    # Documentation files                                                  #
    # ------------------------------------------------------------------ #

    def _organize_documentation(self, op_fn, deduplicate_by_hash: bool) -> None:
        doc_dir = self.organized_dir / "documentation"
        doc_dir.mkdir(parents=True, exist_ok=True)

        seen: Dict[str, str] = {}  # hash/key → canonical filename
        self.documentation_map: Dict[str, List[str]] = {}

        # Index already-present docs to avoid re-hashing on repeated runs
        if deduplicate_by_hash:
            for existing in doc_dir.iterdir():
                if existing.is_file():
                    key = file_hash(existing)
                    seen[key] = existing.name
                    self.documentation_map.setdefault(existing.name, []).append(
                        existing.name
                    )

        for root, _, files in os.walk(self.unzipped_dir):
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext not in DOC_EXTENSIONS:
                    continue

                source = Path(root) / fname

                if deduplicate_by_hash:
                    key = file_hash(source)
                else:
                    key = (fname.lower(), source.stat().st_size)

                if key in seen:
                    canonical = seen[key]
                    self.documentation_map.setdefault(canonical, []).append(fname)
                    continue

                # Build a collision-safe destination name
                parent = source.parent.name
                safe_name = slugify(fname) if parent in fname else f"{parent}_{fname}"
                dest = doc_dir / safe_name
                counter = 1
                while dest.exists():
                    stem, _, suf = safe_name.rpartition(".")
                    dest = doc_dir / (
                        f"{stem}_{counter}.{suf}" if suf else f"{safe_name}_{counter}"
                    )
                    counter += 1

                op_fn(source, dest)
                seen[key] = dest.name
                self.documentation_map.setdefault(dest.name, []).append(fname)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _resolve_module_name(self, year: str, module_code: str) -> str:
        try:
            mask = (self.modules_df["year"].astype(str) == year) & (
                self.modules_df["module_code"].astype(str).str.zfill(4) == module_code
            )
            match = self.modules_df.loc[mask, "module_name"]
            return match.iloc[0] if not match.empty else "unknown"
        except Exception:
            return "unknown"
