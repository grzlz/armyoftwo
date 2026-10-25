#!/usr/bin/env python3
"""Inserta dashboard_data.json en dashboard_template.html y escribe out/delta_secciones.html,
un tablero autocontenido (sin servidor) para explorar el delta por sección.

Uso: python make_dashboard.py [--data data/processed/dashboard_data.json] [--out out/delta_secciones.html]
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE / "data" / "processed" / "dashboard_data.json"))
    ap.add_argument("--template", default=str(HERE / "dashboard_template.html"))
    ap.add_argument("--out", default=str(HERE / "out" / "delta_secciones.html"))
    a = ap.parse_args()
    data = Path(a.data).read_text(encoding="utf-8").replace("</", "<\\/")
    tpl = Path(a.template).read_text(encoding="utf-8")
    if "__DATA_JSON__" not in tpl:
        print("la plantilla no tiene el marcador __DATA_JSON__", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tpl.replace("__DATA_JSON__", data), encoding="utf-8")
    print(f"escribí {out} ({out.stat().st_size/1e6:.1f} MB)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
