#!/usr/bin/env python3
"""Pre-publish leak scanner for this repository.

Scans every file (text files directly; .zip/.xlsx/.docx/.pptx members; PDF text via pdftotext or pypdf) for
patterns that must never be published: local user paths, e-mail addresses, Google Cloud project numbers,
secrets/tokens, plus anything you add.

    python3 tools/check_sensitive.py                       # scan the whole repo
    python3 tools/check_sensitive.py --deny "acme,acme-prod-123" path/to/dir

Extra denylist terms can also come from the SENSITIVE_DENYLIST environment variable (comma separated) — put your
own project id, username, customer names, app ids there. Exit code 1 when anything is found.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv"}
TEXT_EXT = {".py", ".md", ".json", ".js", ".css", ".html", ".svg", ".sh", ".txt", ".conf", ".toml", ".yaml", ".yml",
            ".csv", ".env", ".example", ".xml", ".vtt", ".ini", ".cfg", ""}

GENERIC = [
    (r"(?<![\w.])/Users/[A-Za-z0-9._-]+", "local macOS user path"),
    (r"(?<![\w.])/home/[a-z][A-Za-z0-9._-]+/", "local Linux user path"),
    (r"[A-Za-z0-9._%+-]+@(?!example\.com)[A-Za-z0-9-]+\.[A-Za-z0-9.-]*[A-Za-z]{2,}", "e-mail address"),
    (r"\b\d{12}\b", "12-digit number (looks like a Cloud project number)"),
    (r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|ya29\.[0-9A-Za-z_-]{20,})",
     "token / API key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
]
# fictional data that legitimately matches a generic rule
ALLOW = [
    r"you@example\.com", r"\b123456789012\b", r"\b0{12}\b",
]


def iter_files(paths: list[Path]):
    for base in paths:
        if base.is_file():
            yield base
            continue
        for p in base.rglob("*"):
            if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(base).parts):
                yield p


def texts_of(p: Path):
    """Yield (label, text) for a file and the readable members inside it."""
    ext = p.suffix.lower()
    try:
        if ext in (".zip", ".xlsx", ".docx", ".pptx"):
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    yield f"{p}!{n}", n          # member names too
                    if n.endswith("/"):
                        continue
                    data = z.read(n)
                    if n.lower().endswith((".zip", ".xlsx")):
                        try:
                            with zipfile.ZipFile(io.BytesIO(data)) as z2:
                                for n2 in z2.namelist():
                                    yield f"{p}!{n}!{n2}", z2.read(n2).decode("utf-8", "ignore")
                        except zipfile.BadZipFile:
                            pass
                    elif n.lower().endswith(".pdf"):
                        yield f"{p}!{n}", pdf_text_bytes(data)
                    else:
                        yield f"{p}!{n}", data.decode("utf-8", "ignore")
        elif ext == ".pdf":
            yield str(p), pdf_text_bytes(p.read_bytes())
        elif ext in TEXT_EXT or p.stat().st_size < 2_000_000 and not looks_binary(p):
            yield str(p), p.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:  # unreadable member: report, don't crash
        yield str(p), f"<<scanner could not read: {exc}>>"


def looks_binary(p: Path) -> bool:
    with open(p, "rb") as f:
        return b"\0" in f.read(4096)


def pdf_text_bytes(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(io.BytesIO(data)).pages)
    except ImportError:
        pass
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-", "-"], input=data, capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "ignore")
    return "<<install pypdf to scan PDF text>>"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--deny", default="", help="extra comma-separated literal terms (case-insensitive)")
    a = ap.parse_args()
    terms = [t.strip() for t in (a.deny + "," + os.environ.get("SENSITIVE_DENYLIST", "")).split(",") if t.strip()]
    rules = [(re.compile(rx), why) for rx, why in GENERIC] + [(re.compile(re.escape(t), re.I), f"denylist: {t}") for t in terms]
    allow = [re.compile(rx) for rx in ALLOW]
    hits = 0
    for p in iter_files(a.paths or [ROOT]):
        if p.resolve() == Path(__file__).resolve():
            continue
        for label, text in texts_of(p):
            for rx, why in rules:
                for m in rx.finditer(text):
                    s = m.group(0)
                    ctx = text[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
                    if any(al.search(s) or al.search(ctx) for al in allow):
                        continue
                    hits += 1
                    print(f"{label}: [{why}] …{ctx}…")
    print(f"\n{hits} finding(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
