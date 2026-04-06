"""
Downloader: handles parallel ZIP download and extraction for a batch of modules.

Responsibilities
----------------
* Download ZIPs (parallel, with curl primary / requests fallback).
* Validate ZIPs (single check after download; no redundant re-validation).
* Extract ZIPs.
* Update the :class:`~perustats.inei.utils.db_utils.DatabaseManager` at each
  step so progress is always persisted correctly.
"""

from __future__ import annotations

import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

import requests
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .constants import BASE_URL
from .utils.db_utils import DatabaseManager
from .utils.file_utils import is_zip_valid

console = Console()


class Downloader:
    """
    Downloads and extracts a list of module rows in parallel.

    Parameters
    ----------
    db:
        A :class:`~perustats.inei.utils.db_utils.DatabaseManager` used to
        record per-file progress.
    parallel_jobs:
        Number of concurrent download threads.
    """

    def __init__(self, db: DatabaseManager, parallel_jobs: int = 2) -> None:
        self.db = db
        self.parallel_jobs = parallel_jobs

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def download_and_extract(
        self,
        rows: List[Dict],
        force: bool = False,
        remove_zip_after_extract: bool = False,
    ) -> None:
        """
        Download + extract every row in *rows* in parallel.

        Parameters
        ----------
        rows:
            List of dicts with at least ``url``, ``path_download``,
            ``path_extract`` keys.
        force:
            Re-download even if the ZIP already exists and is valid.
        remove_zip_after_extract:
            Delete the ZIP file after successful extraction.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Downloading {len(rows)} zips...", total=len(rows)
            )

            with ThreadPoolExecutor(max_workers=self.parallel_jobs) as executor:
                futures = {
                    executor.submit(self._process_row_download, row, force): row
                    for row in rows
                }
                for future in as_completed(futures):
                    row = futures[future]
                    try:
                        future.result()
                    except Exception as exc:
                        console.print(f"[red]Error processing {row.get('url')}: {exc}")
                    finally:
                        progress.update(task, advance=1)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Extracting modules...", total=len(rows))

            for row in rows:
                self._process_row_extract(row, remove_zip_after_extract)
                progress.update(task, advance=1)

    # ------------------------------------------------------------------ #
    # Internal per-row pipeline                                            #
    # ------------------------------------------------------------------ #

    def _process_row_download(self, row: Dict, force: bool) -> None:
        url_path: str = row["url"]  # relative path on INEI host
        full_url: str = BASE_URL["descarga"] + url_path
        zip_path = Path(row["path_download"])

        # ── 1. Download ────────────────────────────────────────────────
        if force:
            self.db.reset_download(url_path)
            if zip_path.exists():
                zip_path.unlink()

        if not zip_path.exists() or not is_zip_valid(zip_path):
            ok = self._download(full_url, zip_path)
            if not ok:
                console.print(f"[red]Failed to download {url_path}")
                return
            self.db.mark_downloaded(url_path, str(zip_path))
        else:
            # Already present and valid — just ensure the DB knows
            self.db.mark_downloaded(url_path, str(zip_path))

    def _process_row_extract(self, row, remove_zip_after_extract: bool) -> None:
        zip_path = Path(row["path_download"])
        extract_path = Path(row["path_extract"])
        url_path: str = row["url"]  # relative path on INEI host

        # ── 2. Extract ─────────────────────────────────────────────────
        if not extract_path.exists():
            extracted = self._extract(zip_path, extract_path)
            if not extracted:
                return
        self.db.mark_unzipped(url_path, str(extract_path))

        # ── 3. Optionally remove ZIP ───────────────────────────────────
        if remove_zip_after_extract and zip_path.exists():
            zip_path.unlink()
            self.db.mark_removed_zip(url_path)

    # ------------------------------------------------------------------ #
    # Download helpers                                                     #
    # ------------------------------------------------------------------ #

    def _download(self, url: str, dest: Path) -> bool:
        """
        Try curl first; fall back to requests on failure or corrupt ZIP.
        Returns True only when *dest* contains a valid ZIP.
        """
        dest.parent.mkdir(parents=True, exist_ok=True)

        # ── attempt 1: curl ────────────────────────────────────────────
        try:
            subprocess.run(
                [
                    "curl",
                    "-s",
                    "-L",
                    url,
                    "-o",
                    str(dest),
                    "-H",
                    "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "-H",
                    "Accept-Language: es,en;q=0.9",
                    "-H",
                    "Connection: keep-alive",
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            pass  # fall through to requests

        if is_zip_valid(dest):
            return True

        # ── attempt 2: requests ────────────────────────────────────────
        if dest.exists():
            dest.unlink()
        try:
            resp = requests.get(url, stream=True, timeout=120)
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(8192):
                    fh.write(chunk)
        except Exception:
            return False

        return is_zip_valid(dest)

    def _extract(self, zip_path: Path, dest: Path) -> bool:
        """Extract *zip_path* into *dest*. Returns True on success."""
        try:
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(dest)
            return True
        except Exception as exc:
            console.print(f"[red]Extraction error ({zip_path.name}): {exc}")
            return False
