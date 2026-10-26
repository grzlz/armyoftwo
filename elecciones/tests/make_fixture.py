#!/usr/bin/env python3
"""Genera CSVs SINTÉTICOS con el formato de las bases de cómputos del INE, solo para probar
el pipeline. No son resultados reales."""
import random, sys
from pathlib import Path
random.seed(7)
out = Path(sys.argv[1])
for _y in ("2021", "2024"):
    (out / _y).mkdir(parents=True, exist_ok=True)
STATES = {1: ("AGUASCALIENTES", 3), 9: ("CIUDAD DE MEXICO", 22), 19: ("NUEVO LEON", 14)}

def votes(ln, swing, year):
    turnout = random.uniform(0.45, 0.72)
    tot = int(ln * turnout)
    pm = min(0.8, max(0.15, random.gauss(0.50, 0.12) + swing))
    po = min(0.7, max(0.05, random.gauss(0.32, 0.10) - swing * 0.7))
    pmc = max(0.01, 1 - pm - po - random.uniform(0.03, 0.08))
    sc = pm + po + pmc
    pm, po, pmc = pm / sc * 0.93, po / sc * 0.93, pmc / sc * 0.93
    m = int(tot * pm); o = int(tot * po); mc = int(tot * pmc)
    def split(n, k):
        cuts = sorted(random.randint(0, n) for _ in range(k - 1)); return [b - a for a, b in zip([0] + cuts, cuts + [n])]
    mor = split(m, 7); opp = split(o, 7)
    others = tot - m - o - mc
    nulos = int(others * 0.6); cnr = int(others * 0.02); ci = 0
    rest = others - nulos - cnr - ci
    row = {"PAN": opp[0], "PRI": opp[1], "PRD": opp[2], "PVEM": mor[0], "PT": mor[1], "MC": mc, "MORENA": mor[2],
           "PAN_PRI_PRD": opp[3], "PAN_PRI": opp[4], "PAN_PRD": opp[5], "PRI_PRD": opp[6],
           "PVEM_PT_MORENA": mor[3], "PVEM_PT": mor[4], "PVEM_MORENA": mor[5], "PT_MORENA": mor[6]}
    if year == 2021:
        row["PES"] = rest // 3; row["RSP"] = rest // 3; row["FXM"] = rest - 2 * (rest // 3)
    else:
        ci = rest
    return row, nulos, cnr, ci, tot, ln

secs = []
for ent, (name, nd) in STATES.items():
    n = {1: 600, 9: 1200, 19: 900}[ent]
    for s in range(1, n + 1):
        secs.append((ent, name, random.randint(1, nd), s, random.randint(300, 3500), random.choice([1, 1, 1, 2, 3, 4]), random.gauss(0, 0.05)))

# 2021: coma, latin-1, 1 línea de preámbulo. Columnas estilo 2021.
h21 = ["CLAVE_CASILLA", "CLAVE_ACTA", "ID_ESTADO", "NOMBRE_ESTADO", "ID_DISTRITO", "CABECERA_DISTRITAL", "SECCION", "ID_CASILLA", "TIPO_CASILLA", "EXT_CONTIGUA", "TIPO_ACTA",
       "PAN", "PRI", "PRD", "PVEM", "PT", "MC", "MORENA", "PES", "RSP", "FXM", "PAN_PRI_PRD", "PAN_PRI", "PAN_PRD", "PRI_PRD", "PVEM_PT_MORENA", "PVEM_PT", "PVEM_MORENA", "PT_MORENA",
       "CANDIDATO/A INDEPENDIENTE", "CANDIDATO/A NO REGISTRADO/A", "VOTOS NULOS", "TOTAL_VOTOS_CALCULADOS", "LISTA_NOMINAL", "OBSERVACIONES"]
h24 = ["CLAVE_CASILLA", "CLAVE_ACTA", "ID_ENTIDAD", "ENTIDAD", "ID_DISTRITO_FEDERAL", "DISTRITO_FEDERAL", "SECCION", "ID_CASILLA", "TIPO_CASILLA", "EXT_CONTIGUA", "UBICACION_CASILLA", "TIPO_ACTA",
       "PAN", "PRI", "PRD", "PVEM", "PT", "MC", "MORENA", "PAN_PRI_PRD", "PAN_PRI", "PAN_PRD", "PRI_PRD", "PVEM_PT_MORENA", "PVEM_PT", "PVEM_MORENA", "PT_MORENA",
       "CANDIDATO/A INDEPENDIENTE", "CANDIDATO/A NO REGISTRADO/A", "VOTOS NULOS", "TOTAL_VOTOS_CALCULADOS", "LISTA_NOMINAL", "OBSERVACIONES", "MECANISMOS_TRASLADO", "FECHA_HORA"]
f21 = open(out / "2021" / "Diputaciones.csv", "w", encoding="latin-1", newline="")
f24 = open(out / "2024" / "DIP_FED_2024.csv", "w", encoding="utf-8-sig", newline="")
f21.write("10/06/2021 18:00 (UTC-5)\n" + ",".join(h21) + "\n")
f24.write("11/06/2024 20:00 (UTC-6)\n\n" + "|".join(h24) + "\n")
for ent, name, dist, sec, ln, ncas, swing in secs:
    drop21 = random.random() < 0.01; drop24 = random.random() < 0.01
    for k in range(ncas):
        lnk = ln // ncas
        tipo = "B" if k == 0 else "C"
        if not drop21:
            r, nulos, cnr, ci, tot, _ = votes(lnk, swing, 2021)
            vals = [f"{ent:02d}{sec:04d}{tipo}{k:02d}", f"{ent:02d}{sec:04d}{tipo}{k:02d}1", ent, name, dist, "CABECERA", sec, k + 1, tipo, 0, 1,
                    r["PAN"], r["PRI"], r["PRD"], r["PVEM"], r["PT"], r["MC"], r["MORENA"], r["PES"], r["RSP"], r["FXM"], r["PAN_PRI_PRD"], r["PAN_PRI"], r["PAN_PRD"], r["PRI_PRD"],
                    r["PVEM_PT_MORENA"], r["PVEM_PT"], r["PVEM_MORENA"], r["PT_MORENA"], ci, cnr, nulos, tot, lnk, ""]
            f21.write(",".join(map(str, vals)) + "\n")
        if not drop24:
            r, nulos, cnr, ci, tot, _ = votes(lnk, swing + 0.03 + (0.04 if ent == 19 else -0.02 if ent == 9 else 0), 2024)
            dist24 = min(dist, STATES[ent][1])
            base = [f"{ent:02d}{sec:04d}{tipo}{k:02d}", f"{ent:02d}{sec:04d}{tipo}{k:02d}4", ent, name, dist24, "CABECERA", sec, k + 1, tipo, 0, "URBANA", 4,
                    r["PAN"], r["PRI"], r["PRD"], r["PVEM"], r["PT"], r["MC"], r["MORENA"], r["PAN_PRI_PRD"], r["PAN_PRI"], r["PAN_PRD"], r["PRI_PRD"],
                    r["PVEM_PT_MORENA"], r["PVEM_PT"], r["PVEM_MORENA"], r["PT_MORENA"], ci, cnr, nulos, tot, lnk, "", "", "2024-06-05 10:00"]
            f24.write("|".join(map(str, base)) + "\n")
            if k == 0 and sec % 97 == 0:  # casilla especial con acta RP duplicada
                base2 = list(base); base2[8] = "S"; base2[11] = 5
                f24.write("|".join(map(str, base2)) + "\n")
f21.close(); f24.close()
print("fixture listo:", out)
