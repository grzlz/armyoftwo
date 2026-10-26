#!/usr/bin/env python3
"""Prueba de punta a punta sin red: genera datos SINTÉTICOS en formato INE, levanta un servidor local que imita
el API del SICEE, y corre fetch_ine.py -> build_delta.py -> make_dashboard.py. Verifica que la ruta SICEE (por
sección) y la ruta de cómputos (por acta) producen la misma base SQLite.

Uso: python tests/test_pipeline.py
"""
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

T = Path(__file__).resolve().parent
ROOT = T.parent


def run(*args, ok=(0,)):
    r = subprocess.run([sys.executable, "-I", *map(str, args)], capture_output=True, text=True)
    if r.returncode not in ok:
        sys.exit(f"FALLÓ {args}\n{r.stdout}\n{r.stderr}")
    return r.stderr + r.stdout


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        run(T / "make_fixture.py", d / "computos")
        run(T / "make_sicee_fixture.py", d / "computos", d / "server")
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
        srv = subprocess.Popen([sys.executable, "-I", T / "mock_sicee.py", d / "server", str(port)])
        try:
            time.sleep(0.8)
            api = f"http://127.0.0.1:{port}/api/v1/local/downloads/getCargosElecciones"
            dl = f"http://127.0.0.1:{port}/ACTASSICEEN2024/download/"
            out = run(ROOT / "fetch_ine.py", "--api", api, "--descarga", dl, "--out", d / "raw")
            assert "DIPUTACIONES_FED_MR_2024.zip" in out, out
            assert "RP" not in "".join(p.name for p in (d / "raw").rglob("*.zip")), "bajó un archivo que no es MR"
        finally:
            srv.terminate()
        run(ROOT / "build_delta.py", "--raw", d / "raw", "--db", d / "sicee.sqlite")
        run(ROOT / "build_delta.py", "--raw", d / "computos", "--db", d / "computos.sqlite", "--csv", d / "csv")
        again = run(ROOT / "build_delta.py", "--raw", d / "computos", "--db", d / "computos.sqlite")
        assert again.count("lo omito") == 2, "la segunda carga debió omitir archivos sin cambios"
        a, b = sqlite3.connect(d / "computos.sqlite"), sqlite3.connect(d / "sicee.sqlite")
        for q in ("SELECT anio, clave, distrito, casillas, lista_nominal, total_votos, nulos, cnr, ci FROM secciones ORDER BY 1, 2",
                  "SELECT anio, clave, bloque, votos, pct FROM bloques_seccion ORDER BY 1, 2, 3",
                  "SELECT * FROM resumen_entidad ORDER BY 1, 2, 3, 5"):
            assert a.execute(q).fetchall() == b.execute(q).fetchall(), f"difieren: {q}"
        assert b.execute("SELECT COUNT(*) FROM fuentes WHERE formato = 'sicee_seccion' AND url LIKE 'http%'").fetchone()[0] == 2
        assert b.execute("SELECT COUNT(*) FROM secciones WHERE dif_cuadre <> 0").fetchone()[0] == 0
        nat = dict(b.execute("SELECT bloque, d_pp FROM resumen_nacional WHERE anio_base = 2021 AND anio_objetivo = 2024"))
        assert abs(nat["MORENA_ALIADOS"] - 2.935) < 0.01, nat
        assert (d / "csv" / "delta_seccion_2021_2024.csv").exists()
        run(ROOT / "make_dashboard.py", "--db", d / "sicee.sqlite", "--out", d / "tablero.html")
        assert "__DATA_JSON__" not in (d / "tablero.html").read_text(encoding="utf-8")
    print("OK: fetch (API simulado) -> SQLite -> tablero; SICEE y cómputos coinciden")
    return 0


if __name__ == "__main__":
    sys.exit(main())
