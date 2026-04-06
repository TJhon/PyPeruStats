"""
HTTP helpers: URL encoding and curl-based form POST execution.
"""

from __future__ import annotations

import subprocess
from urllib.parse import quote


def url_encode_survey_name(name: str) -> str:
    """URL-encode *name* using ISO-8859-1 as required by the INEI portal."""
    return quote(name, encoding="iso-8859-1")


def fetch_html(url: str, data: str) -> str:
    """
    Execute a ``curl`` POST to *url* with form *data* and return the decoded
    HTML body.

    Using ``subprocess`` + curl keeps the session handling identical to the
    original implementation and avoids replicating browser-cookie logic in
    ``requests``.
    """
    cmd = ["curl", url, "--data-raw", data]
    result = subprocess.run(cmd, capture_output=True)
    return result.stdout.decode("utf-8", errors="ignore")
