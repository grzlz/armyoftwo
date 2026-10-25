#!/usr/bin/env python3
"""Descarga las bases de datos de Cómputos Distritales del INE (diputaciones federales).

El INE publica la base de cada elección como un ZIP en la pestaña "Base de datos" del
sitio de cómputos. Los nombres de archivo cambian entre elecciones, así que este script
carga la página, localiza todos los enlaces .zip y descarga los que parecen de
diputaciones. Si la página no se puede leer (red bloqueada, sitio caído), descarga el
ZIP a mano y colócalo en data/raw/ (ver README.md).

Uso:
    python fetch_ine.py --years 2021 2024
    python fetch_ine.py --url https://computos2024.ine.mx/.../DIP_FED_2024.zip --year 2024
"""
import argparse
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

PAGES = {
    2018: "https://computos2018.ine.mx/#/descargaBase",
    2021: "https://computos2021.ine.mx/base-de-datos",
    2024: "https://computos2024.ine.mx/base-de-datos",
}
UA = {"User-Agent": "Mozilla/5.0 (compatible; armyoftwo-elecciones/1.0)"}


def fetch(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def find_zip_links(page_url: str) -> list[str]:
    html = fetch(page_url).decode("utf-8", errors="replace")
    hrefs = re.findall(r"""(?:href|src)\s*=\s*["']([^"']+\.zip)["']""", html, flags=re.I)
    hrefs += re.findall(r"""["'](https?://[^"']+\.zip)["']""", html, flags=re.I)
    seen, out = set(), []
    for h in hrefs:
        full = urljoin(page_url, h)
        if full not in seen:
            seen.add(full)
            out.append(full)
    return out


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        total = 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            total += len(chunk)
            print(f"\r  {dest.name}: {total/1e6:,.1f} MB", end="", file=sys.stderr)
    print(file=sys.stderr)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", nargs="*", type=int, default=[2021, 2024])
    ap.add_argument("--url", help="URL directa de un ZIP (omite la búsqueda en la página)")
    ap.add_argument("--year", type=int, help="Año al que pertenece --url")
    ap.add_argument("--out", default=str(Path(__file__).parent / "data" / "raw"))
    ap.add_argument("--all", action="store_true", help="Descarga todos los ZIP, no solo diputaciones")
    a = ap.parse_args()
    out = Path(a.out)

    if a.url:
        if not a.year:
            ap.error("--url requiere --year")
        download(a.url, out / str(a.year) / Path(a.url).name)
        return 0

    rc = 0
    for y in a.years:
        page = PAGES.get(y)
        if not page:
            print(f"[{y}] sin página conocida; usa --url", file=sys.stderr)
            rc = 1
            continue
        try:
            links = find_zip_links(page)
        except Exception as e:  # noqa: BLE001
            print(f"[{y}] no se pudo leer {page}: {e}\n      Descarga el ZIP a mano y guárdalo en {out/str(y)}/", file=sys.stderr)
            rc = 1
            continue
        if not a.all:
            links = [l for l in links if re.search(r"dip", Path(l).name, re.I)]
        if not links:
            print(f"[{y}] la página no expone enlaces .zip de diputaciones (puede ser una app JS). Descarga a mano desde {page}", file=sys.stderr)
            rc = 1
            continue
        for l in links:
            print(f"[{y}] {l}", file=sys.stderr)
            download(l, out / str(y) / Path(l).name)
    return rc


if __name__ == "__main__":
    sys.exit(main())
