"""Rasterize every page of a PDF to PNG using macOS `sips` (CoreGraphics renders the REAL PDF incl.
embedded fonts). pypdf splits the PDF into one-page PDFs because sips only renders page 1.

usage: python3 tools/pdf_pages.py <in.pdf> <out_dir> [width_px]
(pdftoppm is blocked by the endpoint policy on this machine; the swift/PDFKit route fails with CLT.)
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

from pypdf import PdfReader, PdfWriter


def rasterize(pdf: pathlib.Path, out_dir: pathlib.Path, width: int = 900) -> list[pathlib.Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(pdf)
    outs = []
    for i, page in enumerate(reader.pages, start=1):
        one = out_dir / f"_{pdf.stem}_{i:02d}.pdf"
        w = PdfWriter()
        w.add_page(page)
        with one.open("wb") as fh:
            w.write(fh)
        png = out_dir / f"{pdf.stem}-{i:02d}.png"
        subprocess.run(["sips", "-s", "format", "png", "--resampleWidth", str(width), str(one), "--out", str(png)],
                       check=True, capture_output=True)
        one.unlink()
        outs.append(png)
    return outs


if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2])
    wpx = int(sys.argv[3]) if len(sys.argv) > 3 else 900
    for p in rasterize(src, dst, wpx):
        print(p)
