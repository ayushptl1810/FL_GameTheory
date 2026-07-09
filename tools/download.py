"""Download PDFs with retry logic and size validation."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path


def download_pdf(url: str, dest: Path, retries: int = 3) -> bool:
    """Download a PDF to dest. Returns True on success."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 FL-corpus-preloader/1.0",
                    "Accept": "application/pdf,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read()

            if len(content) < 4096:
                return False

            dest.write_bytes(content)
            return True

        except urllib.error.HTTPError as e:
            if e.code == 403:
                # Paywalled — don't retry
                return False
            if attempt < retries - 1:
                time.sleep(4 * (attempt + 1))
        except Exception:
            if attempt < retries - 1:
                time.sleep(4 * (attempt + 1))

    return False
