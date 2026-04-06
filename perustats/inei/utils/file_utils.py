"""
File-system utilities: hashing, zip validation, filename sanitisation.
"""

import hashlib
import re
import unicodedata
import zipfile
from pathlib import Path


def slugify(text: str) -> str:
    """
    Convert *text* to a safe, lowercase, underscore-separated filename stem.

    Steps: NFD-normalise → strip combining marks → remove non-word chars →
    collapse whitespace → lowercase.
    """
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s\-]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text.lower()


def file_hash(path: Path, chunk_size: int = 1 << 20) -> str:
    """Return the SHA-256 hex digest of *path* (streamed, memory-safe)."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def is_zip_valid(path: str | Path) -> bool:
    """
    Return ``True`` when *path* exists and is a non-corrupted ZIP archive.
    ``zipfile.ZipFile.testzip()`` returns ``None`` on success.
    """
    try:
        with zipfile.ZipFile(path, "r") as zf:
            return zf.testzip() is None
    except (zipfile.BadZipFile, FileNotFoundError, OSError):
        return False
