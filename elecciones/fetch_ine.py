#!/usr/bin/env python3
"""Descarga programática de resultados electorales del INE.

Fuente por defecto: SICEE (Sistema de Consulta de la Estadística de las Elecciones, sicee.ine.mx).
El sitio del SICEE es una app web que pide la lista de archivos a un API JSON y luego descarga ZIP
estáticos. Este script hace las mismas dos llamadas:

  1. POST {api}/getCargosElecciones  con {"tipo": "FEDERALES_", "anio": 2024}
     -> lista de archivos [{"nombre": ..., "ruta_zip": ..., ...}]
  2. GET  {descarga}/FEDERALES_2024/<ruta_zip>
     -> ZIP con CSV por entidad, distrito, municipio, sección (_SEC) y casilla (_CAS)

El API no está documentado por el INE; los endpoints vienen de lo que usa el propio sitio y de
github.com/ManuelCadena/inteligencia-electoral-mexico (scripts/download_sicee.py). Si el INE los
cambia, pásalos con --api y --descarga.

Respaldo: --fuente computos busca los ZIP en la página "Base de datos" de computosAAAA.ine.mx, y --url
descarga cualquier ZIP directo.

Cada descarga queda en data/raw/<año>/ y se anota en data/raw/descargas.csv (url, sha256, fecha);
build_delta.py usa ese manifiesto para guardar la URL de origen en la base SQLite.

Uso:
    python fetch_ine.py                                    # SICEE, diputaciones MR, 2021 y 2024
    python fetch_ine.py --years 2018 2021 2024
    python fetch_ine.py --years 2024 --listar              # solo muestra qué archivos ofrece el INE
    python fetch_ine.py --years 2024 --cargo PRESIDENCIA
    python fetch_ine.py --fuente computos --years 2024
    python fetch_ine.py --url https://.../archivo.zip --year 2024
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

HERE = Path(__file__).parent
SICEE_API = "https://sicee-api.ine.mx/api/v1/local/downloads/getCargosElecciones"
SICEE_DESCARGA = "https://sicee.ine.mx/ACTASSICEEN2024/download/"
COMPUTOS_PAGES = {
    2018: "https://computos2018.ine.mx/#/descargaBase",
    2021: "https://computos2021.ine.mx/base-de-datos",
    2024: "https://computos2024.ine.mx/base-de-datos",
}
UA = {"User-Agent": "Mozilla/5.0 (compatible; armyoftwo-elecciones/1.0)"}
RETRIES = 4  # espera 2, 4, 8, 16 s


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def norm(s: object) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s.upper()).strip("_")


def request(url: str, body: dict | None = None, timeout: int = 60):
    data = json.dumps(body).encode() if body is not None else None
    headers = dict(UA, **({"Content-Type": "application/json", "Accept": "application/json"} if body is not None else {}))
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if body is not None else "GET")
    for attempt in range(RETRIES + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == RETRIES:
                raise
            err = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == RETRIES:
                raise
            err = e
        wait = 2 ** (attempt + 1)
        log(f"  reintento en {wait}s ({err})")
        time.sleep(wait)


def download(url: str, dest: Path, force: bool = False) -> tuple[Path, bool]:
    """Descarga url a dest. Devuelve (ruta, True si se descargó; False si ya existía)."""
    if dest.exists() and not force and (dest.suffix.lower() != ".zip" or zipfile.is_zipfile(dest)):
        log(f"  ya existe {dest} (usa --force para bajarlo de nuevo)")
        return dest, False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with request(url, timeout=300) as r, open(tmp, "wb") as f:
        total = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            total += len(chunk)
            print(f"\r  {dest.name}: {total / 1e6:,.1f} MB", end="", file=sys.stderr)
    print(file=sys.stderr)
    if dest.suffix.lower() == ".zip" and not zipfile.is_zipfile(tmp):
        head = tmp.read_bytes()[:200].decode("utf-8", "replace")
        tmp.unlink()
        raise RuntimeError(f"{url} no devolvió un ZIP válido (inicio de la respuesta: {head!r})")
    tmp.replace(dest)
    return dest, True


def record(manifest: Path, year: int, url: str, path: Path, fuente: str) -> None:
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    new = not manifest.exists()
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["anio", "fuente", "url", "archivo", "bytes", "sha256", "descargado_en"])
        w.writerow([year, fuente, url, str(path.resolve()), path.stat().st_size, h,
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")])


# ---------------------------------------------------------------- SICEE
def sicee_list(api: str, year: int, ambito: str) -> list[dict]:
    with request(api, {"tipo": ambito, "anio": year}) as r:
        data = json.load(r)
    if isinstance(data, dict):  # por si el API envuelve la lista
        data = next((v for v in data.values() if isinstance(v, list)), data)
    if not isinstance(data, list):
        raise RuntimeError(f"respuesta inesperada del API para {year}: {str(data)[:300]}")
    return data


def sicee_url(base: str, item: dict, year: int, ambito: str) -> str:
    ruta = item.get("ruta_zip") or item.get("rutaZip") or item.get("archivo")
    if not ruta:
        raise RuntimeError(f"el API no trae 'ruta_zip' en {item}")
    carpeta = f"FEDERALES_{year}" if ambito == "FEDERALES_" else f"{item.get('tipo_ambito', ambito)}/{year}"
    return urljoin(base, f"{carpeta}/{urllib.parse.quote(ruta)}")


def run_sicee(a, out: Path) -> int:
    rc = 0
    want = norm(a.cargo)
    for y in a.years:
        try:
            items = sicee_list(a.api, y, a.ambito)
        except Exception as e:  # noqa: BLE001
            log(f"[{y}] no pude consultar el API del SICEE ({a.api}): {e}")
            rc = 1
            continue
        if not items:
            log(f"[{y}] el SICEE no tiene archivos {a.ambito} para ese año")
            rc = 1
            continue
        match = [it for it in items if want in norm(it.get("ruta_zip", "")) or want in norm(it.get("nombre", ""))]
        if a.listar or not match:
            if not match:
                log(f"[{y}] ningún archivo coincide con --cargo {a.cargo!r}; el INE ofrece:")
                rc = 1
            for it in items:
                print(f"{y}  {it.get('nombre', ''):<45}  {sicee_url(a.descarga, it, y, a.ambito)}")
            continue
        for it in match:
            url = sicee_url(a.descarga, it, y, a.ambito)
            log(f"[{y}] {it.get('nombre', '')} <- {url}")
            try:
                p, new = download(url, out / str(y) / Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name, a.force)
                if new:
                    record(out / "descargas.csv", y, url, p, "sicee")
            except Exception as e:  # noqa: BLE001
                log(f"[{y}] falló la descarga: {e}")
                rc = 1
    return rc


# ---------------------------------------------------------------- cómputos (respaldo)
def find_zip_links(page_url: str) -> list[str]:
    with request(page_url) as r:
        html = r.read().decode("utf-8", errors="replace")
    hrefs = re.findall(r"""(?:href|src)\s*=\s*["']([^"']+\.zip)["']""", html, flags=re.I)
    hrefs += re.findall(r"""["'](https?://[^"']+\.zip)["']""", html, flags=re.I)
    return list(dict.fromkeys(urljoin(page_url, h) for h in hrefs))


def run_computos(a, out: Path) -> int:
    rc = 0
    for y in a.years:
        page = COMPUTOS_PAGES.get(y)
        if not page:
            log(f"[{y}] sin página de cómputos conocida; usa --url")
            rc = 1
            continue
        try:
            links = [l for l in find_zip_links(page) if a.cargo == "*" or "DIP" in norm(Path(l).name) or "COMPUTOS" in norm(Path(l).name)]
        except Exception as e:  # noqa: BLE001
            log(f"[{y}] no se pudo leer {page}: {e}")
            rc = 1
            continue
        if not links:
            log(f"[{y}] la página no expone enlaces .zip en su HTML (es una app JS). Copia la URL del botón de descarga y usa --url")
            rc = 1
        for l in links:
            log(f"[{y}] {l}")
            p, new = download(l, out / str(y) / Path(l).name, a.force)
            if new:
                record(out / "descargas.csv", y, l, p, "computos")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fuente", choices=["sicee", "computos"], default="sicee")
    ap.add_argument("--years", nargs="+", type=int, default=[2021, 2024])
    ap.add_argument("--cargo", default="DIPUTACIONES_FED_MR",
                    help="texto a buscar en el nombre del archivo del SICEE (p. ej. PRESIDENCIA, SENADUR)")
    ap.add_argument("--ambito", default="FEDERALES_", help="FEDERALES_ o LOCALES (SICEE)")
    ap.add_argument("--listar", action="store_true", help="solo lista los archivos disponibles")
    ap.add_argument("--api", default=SICEE_API)
    ap.add_argument("--descarga", default=SICEE_DESCARGA)
    ap.add_argument("--url", help="URL directa de un ZIP o CSV (omite la búsqueda)")
    ap.add_argument("--year", type=int, help="año al que pertenece --url")
    ap.add_argument("--out", default=str(HERE / "data" / "raw"))
    ap.add_argument("--force", action="store_true", help="descarga aunque el archivo ya exista")
    a = ap.parse_args()
    out = Path(a.out)

    if a.url:
        if not a.year:
            ap.error("--url requiere --year")
        p, new = download(a.url, out / str(a.year) / Path(urllib.parse.urlparse(a.url).path).name, a.force)
        if new:
            record(out / "descargas.csv", a.year, a.url, p, "url")
        return 0
    return run_sicee(a, out) if a.fuente == "sicee" else run_computos(a, out)


if __name__ == "__main__":
    sys.exit(main())
