#!/usr/bin/env python3
"""Lee la base SQLite de build_delta.py y escribe out/delta_secciones.html, un tablero autocontenido
(sin servidor) para explorar el delta por sección entre dos años cargados.

Uso: python make_dashboard.py [--db data/elecciones.sqlite] [--base 2021] [--target 2024] [--out out/delta_secciones.html]
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent


def payload(con: sqlite3.Connection, base: int, target: int) -> dict:
    years = {r[0] for r in con.execute("SELECT anio FROM fuentes")}
    for y in (base, target):
        if y not in years:
            raise SystemExit(f"{y} no está cargado en la base (años: {sorted(years)}). Corre build_delta.py primero.")
    blocs = con.execute(
        "SELECT c.bloque, c.etiqueta, b.partidos FROM bloques_comparables c JOIN bloques b ON b.anio = c.anio_objetivo AND b.bloque = c.bloque "
        "WHERE c.anio_base = ? AND c.anio_objetivo = ? AND c.bloque <> 'OTROS' ORDER BY c.orden", (base, target)).fetchall()
    if not blocs:
        raise SystemExit(f"no hay bloques comparables entre {base} y {target} (las coaliciones cambiaron)")
    keys = [b[0] for b in blocs]
    votes = {}
    for y in (base, target):
        for clave, bloque, v in con.execute("SELECT clave, bloque, votos FROM bloques_seccion WHERE anio = ?", (y,)):
            votes[(y, clave, bloque)] = v
    rows = []
    for ent, dist, sec, lna, tota, lnb, totb, clave in con.execute(
            "SELECT sa.entidad_id, sb.distrito, sa.seccion, sa.lista_nominal, sa.total_votos, sb.lista_nominal, sb.total_votos, sa.clave "
            "FROM secciones sa JOIN secciones sb ON sb.anio = ? AND sb.clave = sa.clave WHERE sa.anio = ? ORDER BY sa.clave", (target, base)):
        rows.append([ent, dist or 0, sec, lna, tota, *[votes.get((base, clave, k), 0) for k in keys],
                     lnb, totb, *[votes.get((target, clave, k), 0) for k in keys]])
    only = lambda a, b: con.execute(  # noqa: E731
        "SELECT COUNT(*) FROM secciones s WHERE s.anio = ? AND NOT EXISTS (SELECT 1 FROM secciones t WHERE t.anio = ? AND t.clave = s.clave)",
        (a, b)).fetchone()[0]
    sources = {str(y): {"file": f, "preamble": p or "", "rows_in": n, "url": u or ""}
               for y, f, p, n, u in con.execute("SELECT anio, archivo, preambulo, filas_leidas, url FROM fuentes WHERE anio IN (?, ?)", (base, target))}
    return {
        "base": base, "target": target,
        "blocs": [{"key": k, "label": et, "members": p.split(",")} for k, et, p in blocs],
        "states": {str(k): v for k, v in con.execute("SELECT entidad_id, nombre FROM entidades")},
        "cols": ["ent", "dist", "sec", "ln_a", "tot_a", *[f"{k}_a" for k in keys], "ln_b", "tot_b", *[f"{k}_b" for k in keys]],
        "rows": rows, "only_base": only(base, target), "only_target": only(target, base),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "sources": sources,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(HERE / "data" / "elecciones.sqlite"))
    ap.add_argument("--base", type=int, default=2021)
    ap.add_argument("--target", type=int, default=2024)
    ap.add_argument("--template", default=str(HERE / "dashboard_template.html"))
    ap.add_argument("--out", default=str(HERE / "out" / "delta_secciones.html"))
    a = ap.parse_args()
    if not Path(a.db).exists():
        print(f"no existe {a.db}; corre build_delta.py primero", file=sys.stderr)
        return 1
    with sqlite3.connect(f"file:{a.db}?mode=ro", uri=True) as con:
        data = payload(con, a.base, a.target)
    tpl = Path(a.template).read_text(encoding="utf-8")
    if "__DATA_JSON__" not in tpl:
        print("la plantilla no tiene el marcador __DATA_JSON__", file=sys.stderr)
        return 1
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tpl.replace("__DATA_JSON__", blob), encoding="utf-8")
    print(f"escribí {out} ({out.stat().st_size / 1e6:.1f} MB, {len(data['rows']):,} secciones)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
