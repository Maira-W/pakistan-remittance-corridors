"""Download the raw files once and record a checksum, source and date for each in data/raw/MANIFEST.json.

    python -m remit ingest          download what is missing
    python -m remit ingest --refresh  download everything again
    python -m remit verify          check the files against the manifest
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from . import config

USER_AGENT = "Mozilla/5.0 (research project; pakistan-remittance-corridors)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _load() -> dict:
    return json.loads(config.MANIFEST.read_text(encoding="utf-8")) if config.MANIFEST.exists() else {"files": {}}


def _download(url: str, dest: Path, magic: bytes, tries: int = 12) -> None:
    """Fetch with curl, resuming a partial file: the State Bank's server is slow and drops long transfers."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(tries):
        subprocess.run(["curl", "-s", "-L", "-A", USER_AGENT, "-C", "-", "--max-time", "120", "-o", str(dest), url],
                       check=False)
        if dest.exists() and dest.stat().st_size > 0 and dest.read_bytes()[:len(magic)] == magic:
            head = subprocess.run(["curl", "-s", "-L", "-I", "-A", USER_AGENT, "--max-time", "30", url],
                                  capture_output=True, text=True).stdout.lower()
            total = next((int(line.split(":")[1]) for line in head.splitlines() if line.startswith("content-length")), None)
            if total is None or dest.stat().st_size >= total:
                return
        time.sleep(2)
    raise RuntimeError(f"could not download {url}")


def _extract_page(pdf_path: Path, page_number: int, dest: Path) -> None:
    import pypdfium2 as pdfium
    src = pdfium.PdfDocument(str(pdf_path))
    out = pdfium.PdfDocument.new()
    out.import_pages(src, [page_number - 1])
    out.save(str(dest))


def run(refresh: bool = False, bulletin_file: Path | None = None) -> dict:
    manifest = _load()
    files = manifest["files"]

    archive = config.RAW / config.ARCHIVE_FILE
    if refresh or not archive.exists():
        print("[ingest] SBP country-wise workbook (Internet Archive copy) ...", flush=True)
        _download(config.ARCHIVE_URL, archive, b"PK")
    files[config.ARCHIVE_FILE] = {
        "sha256": sha256(archive), "bytes": archive.stat().st_size, "source": config.ARCHIVE_URL,
        "note": "SBP workbook 'Homeremit_Arch.xlsx', saved by the Internet Archive on 2024-06-01 (monthly, by country).",
        "retrieved_utc": files.get(config.ARCHIVE_FILE, {}).get("retrieved_utc") or datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
    }

    page = config.RAW / config.BULLETIN_FILE
    if refresh or not page.exists():
        print("[ingest] SBP Monthly Statistical Bulletin, August 2026 (7 MB, slow) ...", flush=True)
        full = bulletin_file or (config.RAW / "sbp" / "_bulletin_full.pdf")
        if bulletin_file is None:
            _download(config.BULLETIN_URL, full, b"%PDF")
        _extract_page(full, config.BULLETIN_PAGE, page)
        files[config.BULLETIN_FILE] = {
            "sha256": sha256(page), "bytes": page.stat().st_size, "source": config.BULLETIN_URL,
            "note": f"Page {config.BULLETIN_PAGE} (table 4.8) of the full bulletin, whose own SHA-256 was {sha256(full)}; "
                    "only this page is stored.",
            "retrieved_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
        }
        if bulletin_file is None:
            full.unlink()
    manifest["files"] = dict(sorted(files.items()))
    config.MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"[ingest] manifest lists {len(manifest['files'])} files")
    return manifest


def verify() -> list[str]:
    """Return the problems found: a missing file, or a file whose checksum differs from the manifest."""
    problems = []
    for rel, info in _load()["files"].items():
        path = config.RAW / rel
        if not path.exists():
            problems.append(f"missing: {rel}")
        elif sha256(path) != info["sha256"]:
            problems.append(f"changed: {rel}")
    return problems
