#!/usr/bin/env python3
"""Convierte el fixture SINTÉTICO de cómputos (por acta) al formato SICEE por sección y lo empaqueta como lo
sirve el INE: un ZIP por cargo con CSV _ENT/_DIS/_SEC y de candidaturas. Solo para pruebas."""
import io, sys, zipfile
from pathlib import Path
import pandas as pd
src, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
NAMES = {1: "AGUASCALIENTES", 9: "CIUDAD DE MÉXICO", 19: "NUEVO LEÓN"}
specs = {2021: (src / "2021/Diputaciones.csv", ",", 1, "latin-1", "ID_ESTADO", "ID_DISTRITO", None),
         2024: (src / "2024/DIP_FED_2024.csv", "|", 2, "utf-8-sig", "ID_ENTIDAD", "ID_DISTRITO_FEDERAL", 4)}
for y, (f, sep, skip, enc, ecol, dcol, acta) in specs.items():
    df = pd.read_csv(f, sep=sep, skiprows=skip, encoding=enc)
    if acta: df = df[df.TIPO_ACTA == acta]
    party = [c for c in df.columns if c.replace("_", "").isalpha() and c.upper() == c and all(t in {"PAN","PRI","PRD","PVEM","PT","MC","MORENA","PES","RSP","FXM"} for t in c.split("_"))]
    df["CASILLAS"] = 1
    g = df.groupby([ecol, "SECCION"]).agg({dcol: "max", "CASILLAS": "sum", **{c: "sum" for c in party},
        "CANDIDATO/A INDEPENDIENTE": "sum", "CANDIDATO/A NO REGISTRADO/A": "sum", "VOTOS NULOS": "sum",
        "TOTAL_VOTOS_CALCULADOS": "sum", "LISTA_NOMINAL": "sum"}).reset_index()
    sec = pd.DataFrame({"CIRCUNSCRIPCION": 2, "ID_ESTADO": g[ecol], "NOMBRE_ESTADO": g[ecol].map(NAMES), "ID_DISTRITO": g[dcol],
        "DISTRITO": "CABECERA", "ID_MUNICIPIO": 1, "MUNICIPIO": "MUNICIPIO", "SECCION": g.SECCION, "CASILLAS": g.CASILLAS})
    for c in party: sec[c] = g[c]
    sec["CAND_IND_1"] = g["CANDIDATO/A INDEPENDIENTE"]; sec["NUM_VOTOS_CAN_NREG"] = g["CANDIDATO/A NO REGISTRADO/A"]
    sec["NUM_VOTOS_NULOS"] = g["VOTOS NULOS"]; sec["NUM_VOTOS_VALIDOS"] = g.TOTAL_VOTOS_CALCULADOS - g["VOTOS NULOS"]
    sec["TOTAL_VOTOS"] = g.TOTAL_VOTOS_CALCULADOS; sec["LISTA_NOMINAL"] = g.LISTA_NOMINAL; sec["OBSERVACIONES"] = ""
    total = {c: "" for c in sec.columns}; total.update({"NOMBRE_ESTADO": "TOTAL", "TOTAL_VOTOS": int(sec.TOTAL_VOTOS.sum())})
    sec = pd.concat([sec, pd.DataFrame([total])], ignore_index=True)  # pie con totales, como algunos archivos del SICEE
    dis = sec.iloc[:-1].groupby(["ID_ESTADO", "ID_DISTRITO"])[["TOTAL_VOTOS", "LISTA_NOMINAL"] + party].sum().reset_index()
    pre = f"{y}_SEE_DIP_FED_MR_NAL"
    for cargo, files in {f"DIPUTACIONES_FED_MR_{y}.zip": {f"{pre}_SEC.csv": sec, f"{pre}_DIS.csv": dis, f"{pre}_DISCAND.csv": dis.head(5)},
                         f"DIPUTACIONES_FED_RP_{y}.zip": {f"{y}_SEE_DIP_FED_RP_NAL_ENT.csv": dis.head(3)},
                         f"PRESIDENCIA_{y}.zip": {f"{y}_SEE_PRES_NAL_SEC.csv": dis.head(3)}}.items():
        if y == 2021 and cargo.startswith("PRESIDENCIA"): continue
        d = out / f"FEDERALES_{y}"; d.mkdir(exist_ok=True)
        with zipfile.ZipFile(d / cargo, "w", zipfile.ZIP_DEFLATED) as z:
            for name, frame in files.items():
                z.writestr(f"{cargo[:-4]}/{name}", frame.to_csv(index=False).encode("latin-1"))
print("SICEE fixture:", sorted(str(p.relative_to(out)) for p in out.rglob("*.zip")))
