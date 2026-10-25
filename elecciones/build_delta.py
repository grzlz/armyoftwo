#!/usr/bin/env python3
"""Agrega las bases de cómputos del INE (nivel acta/casilla) a nivel SECCIÓN ELECTORAL y
calcula el delta entre dos elecciones.

Clave de sección = entidad (2 dígitos) + sección (4 dígitos), p. ej. 09-0123. Es el nivel
geográfico más fino que el INE publica; no existe información por clave de elector
(voto secreto).

Entrada: los CSV de "Base de datos" de computosYYYY.ine.mx (o sus ZIP) en data/raw/.
Salida (data/processed/):
    secciones_<año>.csv              votos y porcentajes por sección y bloque
    delta_<base>_<objetivo>.csv      cambio por sección (puntos porcentuales)
    resumen_entidad_<base>_<objetivo>.csv
    resumen_distrito_<base>_<objetivo>.csv
    dashboard_data.json              insumo compacto para make_dashboard.py

Uso:
    python build_delta.py                       # 2021 -> 2024
    python build_delta.py --base 2018 --target 2021
    python build_delta.py --file 2021=/ruta/Diputaciones.csv --file 2024=/ruta/DIP_FED_2024.csv
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent

# ---------------------------------------------------------------- configuración
# Alias de columnas de partido -> token canónico. Agrega aquí si un año usa otro nombre.
PARTY_ALIAS = {
    "PAN": "PAN", "PRI": "PRI", "PRD": "PRD", "PVEM": "PVEM", "PT": "PT", "MC": "MC",
    "MORENA": "MORENA", "PES": "PES", "ES": "PES", "ENCUENTRO_SOCIAL": "PES",
    "RSP": "RSP", "FXM": "FXM", "FUERZA_POR_MEXICO": "FXM",
    "NA": "NA", "PNA": "NA", "NVA_ALIANZA": "NA", "NUEVA_ALIANZA": "NA", "PANAL": "NA",
    "PH": "PH", "PSD": "PSD",
}
MULTIWORD = [("NUEVA_ALIANZA", "NA"), ("NVA_ALIANZA", "NA"), ("ENCUENTRO_SOCIAL", "PES"), ("FUERZA_POR_MEXICO", "FXM")]

# Bloques por año. Una columna de coalición (p. ej. PVEM_PT_MORENA) se asigna al bloque
# que contiene a TODOS sus partidos, así el bloque suma votos individuales + combinaciones.
BLOQUES = {
    2024: {"MORENA_ALIADOS": {"MORENA", "PT", "PVEM"}, "PAN_PRI_PRD": {"PAN", "PRI", "PRD"}, "MC": {"MC"}},
    2021: {"MORENA_ALIADOS": {"MORENA", "PT", "PVEM"}, "PAN_PRI_PRD": {"PAN", "PRI", "PRD"}, "MC": {"MC"}},
    # 2018 tuvo coaliciones distintas (PVEM con PRI, MC con PAN-PRD, PES con Morena).
    2018: {"MORENA_PT_PES": {"MORENA", "PT", "PES"}, "PRI_PVEM_NA": {"PRI", "PVEM", "NA"}, "PAN_PRD_MC": {"PAN", "PRD", "MC"}},
}
BLOQUE_LABEL = {
    "MORENA_ALIADOS": "Morena + PT + PVEM", "PAN_PRI_PRD": "PAN + PRI + PRD", "MC": "MC",
    "MORENA_PT_PES": "Morena + PT + PES", "PRI_PVEM_NA": "PRI + PVEM + NA", "PAN_PRD_MC": "PAN + PRD + MC",
}
ENTIDADES = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur", 4: "Campeche", 5: "Coahuila",
    6: "Colima", 7: "Chiapas", 8: "Chihuahua", 9: "Ciudad de México", 10: "Durango", 11: "Guanajuato",
    12: "Guerrero", 13: "Hidalgo", 14: "Jalisco", 15: "México", 16: "Michoacán", 17: "Morelos",
    18: "Nayarit", 19: "Nuevo León", 20: "Oaxaca", 21: "Puebla", 22: "Querétaro", 23: "Quintana Roo",
    24: "San Luis Potosí", 25: "Sinaloa", 26: "Sonora", 27: "Tabasco", 28: "Tamaulipas", 29: "Tlaxcala",
    30: "Veracruz", 31: "Yucatán", 32: "Zacatecas",
}


# ---------------------------------------------------------------- utilidades
def norm(s: object) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s.upper()).strip("_")
    for long, short in MULTIWORD:
        s = s.replace(long, short)
    return s


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def unzip_all(raw: Path) -> None:
    for z in raw.rglob("*.zip"):
        dest = z.with_suffix("")
        if dest.exists():
            continue
        log(f"descomprimiendo {z.name}")
        with zipfile.ZipFile(z) as zf:
            zf.extractall(dest)


def year_of(p: Path) -> int | None:
    for part in [p.name, *[q.name for q in p.parents]]:
        m = re.search(r"(20\d\d)", part)
        if m:
            return int(m.group(1))
    return None


def discover(raw: Path) -> dict[int, Path]:
    """Elige por año el CSV de diputaciones (no el de candidaturas)."""
    found: dict[int, list[Path]] = {}
    for p in raw.rglob("*"):
        if p.suffix.lower() not in (".csv", ".txt"):
            continue
        n = norm(p.stem)
        if "CANDIDAT" in n or "LEEME" in n or "README" in n:
            continue
        if not re.search(r"DIP", n):
            continue
        y = year_of(p)
        if y:
            found.setdefault(y, []).append(p)
    out = {}
    for y, ps in found.items():
        ps.sort(key=lambda q: q.stat().st_size, reverse=True)
        out[y] = ps[0]
        if len(ps) > 1:
            log(f"[{y}] varios candidatos, uso el mayor: {ps[0]} (otros: {[str(q) for q in ps[1:]]})")
    return out


def sniff(path: Path) -> tuple[str, int, str]:
    """Devuelve (encoding, índice de la línea de encabezado, delimitador)."""
    data = path.read_bytes()[:200_000]
    try:
        text, enc = data.decode("utf-8-sig"), "utf-8-sig"
    except UnicodeDecodeError:
        text, enc = data.decode("latin-1"), "latin-1"
    lines = text.splitlines()
    for i, line in enumerate(lines[:60]):
        if "SECCION" in norm(line):
            counts = {d: line.count(d) for d in ("|", ",", ";", "\t")}
            delim = max(counts, key=counts.get)
            if counts[delim] >= 5:
                return enc, i, delim
    raise SystemExit(f"{path}: no encontré una línea de encabezado con SECCION en las primeras 60 líneas")


def read_computos(path: Path) -> tuple[pd.DataFrame, str]:
    enc, hdr, delim = sniff(path)
    preamble = ""
    if hdr > 0:
        with open(path, encoding=enc, errors="replace") as f:
            preamble = " / ".join(next(f).strip() for _ in range(hdr)).strip(" /")
    log(f"leyendo {path.name}: encoding={enc} encabezado=línea {hdr+1} delim={delim!r}")
    df = pd.read_csv(path, sep=delim, skiprows=hdr, encoding=enc, dtype=str, on_bad_lines="warn", engine="python" if delim == "|" and enc == "latin-1" else "c")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, [c for c in df.columns if not c.startswith("Unnamed")]]
    return df, preamble


def classify(cols: list[str]) -> tuple[dict[str, str], dict[str, tuple[str, ...]], list[str], list[str]]:
    roles: dict[str, str] = {}
    party: dict[str, tuple[str, ...]] = {}
    ci: list[str] = []
    unknown: list[str] = []
    for c in cols:
        n = norm(c)
        if n in ("ID_ENTIDAD", "ID_ESTADO", "CLAVE_ENTIDAD", "CVE_ENTIDAD"):
            roles.setdefault("ent_id", c)
        elif n in ("ENTIDAD", "NOMBRE_ESTADO", "NOMBRE_ENTIDAD", "ESTADO"):
            roles.setdefault("ent_name", c)
        elif n in ("ID_DISTRITO_FEDERAL", "ID_DISTRITO", "ID_DISTRITO_FED", "DISTRITO_FEDERAL_ID"):
            roles.setdefault("dist_id", c)
        elif n in ("DISTRITO_FEDERAL", "CABECERA_DISTRITAL_FEDERAL", "CABECERA_DISTRITAL", "DISTRITO", "NOMBRE_DISTRITO"):
            roles.setdefault("dist_name", c)
        elif n == "SECCION":
            roles["seccion"] = c
        elif n in ("ID_MUNICIPIO", "CVE_MUNICIPIO"):
            roles.setdefault("mun_id", c)
        elif n in ("MUNICIPIO", "NOMBRE_MUNICIPIO"):
            roles.setdefault("mun_name", c)
        elif n == "TIPO_ACTA":
            roles["tipo_acta"] = c
        elif n == "TIPO_CASILLA":
            roles["tipo_casilla"] = c
        elif n.startswith("LISTA_NOMINAL"):
            roles.setdefault("ln", c)
        elif n in ("TOTAL_VOTOS_CALCULADOS", "TOTAL_VOTOS_CALCULADO"):
            roles["total"] = c
        elif n.startswith("TOTAL_VOTOS"):
            roles.setdefault("total_alt", c)
        elif "NO_REGISTRAD" in n:
            roles.setdefault("cnr", c)
        elif "NULO" in n:
            roles.setdefault("nulos", c)
        elif "INDEPENDIENTE" in n or "CAND_IND" in n or re.fullmatch(r"CI(_?\d+)?", n):
            ci.append(c)
        else:
            toks = [t for t in n.split("_") if t]
            if toks and all(t in PARTY_ALIAS for t in toks):
                party[c] = tuple(sorted({PARTY_ALIAS[t] for t in toks}))
            else:
                unknown.append(c)
    if "total" not in roles and "total_alt" in roles:
        roles["total"] = roles["total_alt"]
    return roles, party, ci, unknown


def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce").fillna(0)


# ---------------------------------------------------------------- agregación por sección
def aggregate(path: Path, year: int) -> tuple[pd.DataFrame, dict]:
    df, preamble = read_computos(path)
    roles, party, ci, unknown = classify(list(df.columns))
    missing = [r for r in ("seccion", "total") if r not in roles]
    if "ent_id" not in roles and "ent_name" in roles and to_num(df[roles["ent_name"]]).gt(0).all():
        roles["ent_id"] = roles["ent_name"]
    if "ent_id" not in roles:
        missing.append("ent_id")
    if missing:
        raise SystemExit(f"[{year}] faltan columnas clave {missing}. Columnas vistas: {list(df.columns)}")
    if not party:
        raise SystemExit(f"[{year}] no reconocí columnas de partido. Columnas: {list(df.columns)}")
    log(f"[{year}] partidos/coaliciones: {list(party)}")
    if unknown:
        log(f"[{year}] columnas ignoradas: {unknown}")

    n0 = len(df)
    # Una sola acta por casilla: en diputaciones las casillas especiales traen acta MR y RP.
    if "tipo_acta" in roles:
        vc = df[roles["tipo_acta"]].value_counts(dropna=False)
        if len(vc) > 1:
            modal = vc.index[0]
            rest = vc.iloc[1:].sum()
            if rest / n0 <= 0.05:
                df = df[df[roles["tipo_acta"]] == modal]
                log(f"[{year}] TIPO_ACTA: conservo {modal!r} ({vc.iloc[0]:,} actas), descarto {rest:,} actas de otros tipos {dict(vc.iloc[1:])}")
            else:
                log(f"[{year}] TIPO_ACTA con varios valores grandes {dict(vc)}; conservo todas (revisa duplicidad MR/RP)")

    ent = to_num(df[roles["ent_id"]]).astype(int)
    sec = to_num(df[roles["seccion"]]).astype(int)
    keep = (ent > 0) & (sec > 0)
    if (~keep).sum():
        log(f"[{year}] descarto {(~keep).sum():,} actas sin entidad/sección válida")
    df = df[keep].copy()
    ent, sec = ent[keep], sec[keep]

    out = pd.DataFrame({"entidad_id": ent.values, "seccion": sec.values})
    out["distrito"] = to_num(df[roles["dist_id"]]).astype(int).values if "dist_id" in roles else 0
    out["lista_nominal"] = to_num(df[roles["ln"]]).values if "ln" in roles else 0
    out["total_votos"] = to_num(df[roles["total"]]).values
    out["nulos"] = to_num(df[roles["nulos"]]).values if "nulos" in roles else 0
    out["cnr"] = to_num(df[roles["cnr"]]).values if "cnr" in roles else 0
    out["ci"] = sum((to_num(df[c]) for c in ci), start=pd.Series(0.0, index=df.index)).values
    pcols = []
    for c in party:
        name = "v_" + norm(c)
        out[name] = to_num(df[c]).values
        pcols.append(name)
    out["n_actas"] = 1

    sums = {c: "sum" for c in ["n_actas", "lista_nominal", "total_votos", "nulos", "cnr", "ci", *pcols]}
    sums["distrito"] = "max"
    g = out.groupby(["entidad_id", "seccion"], as_index=False).agg(sums)
    g["entidad"] = g["entidad_id"].map(ENTIDADES).fillna(g["entidad_id"].astype(str))
    g["clave"] = g["entidad_id"].map("{:02d}".format) + "-" + g["seccion"].map("{:04d}".format)

    blocs = BLOQUES.get(year)
    if blocs is None:
        raise SystemExit(f"[{year}] define BLOQUES[{year}] en build_delta.py")
    assigned: set[str] = set()
    for b, members in blocs.items():
        cols = ["v_" + norm(c) for c, parts in party.items() if set(parts) <= members]
        g["b_" + b] = g[cols].sum(axis=1) if cols else 0
        assigned.update(cols)
        log(f"[{year}] bloque {b}: {cols}")
    rest = [c for c in pcols if c not in assigned]
    g["b_OTROS"] = g[rest].sum(axis=1) + g["ci"]
    if rest:
        log(f"[{year}] OTROS = {rest} + independientes")
    bcols = ["b_" + b for b in blocs] + ["b_OTROS"]
    g["check_diff"] = g["total_votos"] - g[bcols].sum(axis=1) - g["nulos"] - g["cnr"]
    bad = (g["check_diff"].abs() > 0).sum()
    if bad:
        log(f"[{year}] aviso: en {bad:,} secciones la suma de bloques+nulos+CNR no cuadra con TOTAL_VOTOS (dif. media {g['check_diff'].abs().mean():.2f})")
    tot = g["total_votos"].replace(0, np.nan)
    for b in bcols:
        g["pct_" + b[2:]] = (g[b] / tot * 100).round(3)
    g["participacion"] = (g["total_votos"] / g["lista_nominal"].replace(0, np.nan) * 100).round(3)
    front = ["clave", "entidad_id", "entidad", "distrito", "seccion", "n_actas", "lista_nominal", "total_votos", "participacion", "nulos", "cnr", "ci"]
    g = g[front + bcols + ["pct_" + b[2:] for b in bcols] + pcols]
    meta = {"year": year, "file": str(path), "preamble": preamble, "rows_in": n0, "secciones": len(g),
            "blocs": {b: sorted(m) for b, m in blocs.items()}, "party_cols": {c: list(p) for c, p in party.items()}}
    return g, meta


# ---------------------------------------------------------------- delta
def weighted(df: pd.DataFrame, blocs: list[str], suf_a: str, suf_b: str) -> dict:
    r = {}
    ta, tb = df["total_votos" + suf_a].sum(), df["total_votos" + suf_b].sum()
    for b in blocs:
        pa = df["b_" + b + suf_a].sum() / ta * 100 if ta else np.nan
        pb = df["b_" + b + suf_b].sum() / tb * 100 if tb else np.nan
        r["pct_" + b + suf_a], r["pct_" + b + suf_b], r["d_" + b] = round(pa, 3), round(pb, 3), round(pb - pa, 3)
    la, lb = df["lista_nominal" + suf_a].sum(), df["lista_nominal" + suf_b].sum()
    r["participacion" + suf_a] = round(ta / la * 100, 3) if la else np.nan
    r["participacion" + suf_b] = round(tb / lb * 100, 3) if lb else np.nan
    r["d_participacion"] = round(r["participacion" + suf_b] - r["participacion" + suf_a], 3)
    r["lista_nominal" + suf_a], r["lista_nominal" + suf_b] = int(la), int(lb)
    r["total_votos" + suf_a], r["total_votos" + suf_b] = int(ta), int(tb)
    r["n_secciones"] = int(len(df))
    return r


def build_delta(a: pd.DataFrame, b: pd.DataFrame, ya: int, yb: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    comparable = [k for k, m in BLOQUES[ya].items() if BLOQUES[yb].get(k) == m]
    if not comparable:
        log(f"aviso: los bloques de {ya} y {yb} no coinciden; solo habrá delta de participación y OTROS")
    blocs = comparable + ["OTROS"]
    sa, sb = f"_{ya}", f"_{yb}"
    keys = ["clave", "entidad_id", "entidad", "seccion"]
    a = a.rename(columns={c: c + sa for c in a.columns if c not in keys})
    b = b.rename(columns={c: c + sb for c in b.columns if c not in keys})
    m = a.merge(b, on=keys, how="outer", indicator=True)
    m["estado"] = m["_merge"].map({"both": "ambas", "left_only": f"solo_{ya}", "right_only": f"solo_{yb}"})
    m = m.drop(columns="_merge")
    for b_ in blocs:
        m["d_" + b_] = (m["pct_" + b_ + sb] - m["pct_" + b_ + sa]).round(3)
    m["d_participacion"] = (m["participacion" + sb] - m["participacion" + sa]).round(3)
    m["d_lista_nominal"] = m["lista_nominal" + sb] - m["lista_nominal" + sa]
    m["d_total_votos"] = m["total_votos" + sb] - m["total_votos" + sa]
    both = m[m["estado"] == "ambas"].copy()
    for c in ["lista_nominal", "total_votos", *["b_" + x for x in blocs]]:
        both[c + sa] = both[c + sa].fillna(0)
        both[c + sb] = both[c + sb].fillna(0)
    ent = pd.DataFrame([{"entidad_id": k, "entidad": ENTIDADES.get(k, str(k)), **weighted(grp, blocs, sa, sb)} for k, grp in both.groupby("entidad_id")])
    dist = pd.DataFrame([{"entidad_id": k[0], "entidad": ENTIDADES.get(k[0], str(k[0])), "distrito": int(k[1]), **weighted(grp, blocs, sa, sb)}
                         for k, grp in both.groupby(["entidad_id", "distrito" + sb])])
    return m, ent, dist, blocs


def dashboard_json(m: pd.DataFrame, ya: int, yb: int, blocs: list[str], metas: dict, out: Path) -> None:
    sa, sb = f"_{ya}", f"_{yb}"
    both = m[m["estado"] == "ambas"]
    bl = [b for b in blocs if b != "OTROS"]
    cols = ["ent", "dist", "sec", "ln_a", "tot_a", *[f"{b}_a" for b in bl], "ln_b", "tot_b", *[f"{b}_b" for b in bl]]
    arr = np.column_stack([
        both["entidad_id"], both["distrito" + sb].fillna(0), both["seccion"],
        both["lista_nominal" + sa].fillna(0), both["total_votos" + sa].fillna(0), *[both["b_" + b + sa].fillna(0) for b in bl],
        both["lista_nominal" + sb].fillna(0), both["total_votos" + sb].fillna(0), *[both["b_" + b + sb].fillna(0) for b in bl],
    ]).astype(np.int64)
    payload = {
        "base": ya, "target": yb,
        "blocs": [{"key": b, "label": BLOQUE_LABEL.get(b, b), "members": sorted(BLOQUES[yb][b])} for b in bl],
        "states": {str(k): v for k, v in ENTIDADES.items()},
        "cols": cols, "rows": arr.tolist(),
        "only_base": int((m["estado"] == f"solo_{ya}").sum()), "only_target": int((m["estado"] == f"solo_{yb}").sum()),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "sources": {str(y): {"file": Path(mt["file"]).name, "preamble": mt["preamble"], "rows_in": mt["rows_in"]} for y, mt in metas.items()},
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    log(f"escribí {out} ({out.stat().st_size/1e6:.1f} MB, {len(arr):,} secciones)")


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=str(HERE / "data" / "raw"))
    ap.add_argument("--out", default=str(HERE / "data" / "processed"))
    ap.add_argument("--base", type=int, default=2021)
    ap.add_argument("--target", type=int, default=2024)
    ap.add_argument("--file", action="append", default=[], metavar="AÑO=RUTA", help="CSV explícito por año (repetible)")
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    files: dict[int, Path] = {}
    if raw.exists():
        unzip_all(raw)
        files.update(discover(raw))
    for spec in a.file:
        y, p = spec.split("=", 1)
        files[int(y)] = Path(p)
    for y in (a.base, a.target):
        if y not in files:
            log(f"no hay archivo de diputaciones para {y} en {raw}. Descárgalo (fetch_ine.py o a mano) o pásalo con --file {y}=ruta.csv")
            return 2
    log(f"archivos: { {y: str(p) for y, p in files.items()} }")

    secs, metas = {}, {}
    for y in (a.base, a.target):
        g, meta = aggregate(files[y], y)
        secs[y], metas[y] = g, meta
        g.to_csv(out / f"secciones_{y}.csv", index=False)
        log(f"[{y}] {len(g):,} secciones, {int(g['total_votos'].sum()):,} votos, LN {int(g['lista_nominal'].sum()):,}")

    m, ent, dist, blocs = build_delta(secs[a.base], secs[a.target], a.base, a.target)
    m.to_csv(out / f"delta_{a.base}_{a.target}.csv", index=False)
    ent.to_csv(out / f"resumen_entidad_{a.base}_{a.target}.csv", index=False)
    dist.to_csv(out / f"resumen_distrito_{a.base}_{a.target}.csv", index=False)
    dashboard_json(m, a.base, a.target, blocs, metas, out / "dashboard_data.json")

    both = m[m["estado"] == "ambas"]
    nat = weighted(both.assign(**{c: both[c].fillna(0) for c in both.columns if c.startswith(("b_", "total_votos", "lista_nominal"))}), blocs, f"_{a.base}", f"_{a.target}")
    log("\nResumen nacional (secciones presentes en ambas elecciones):")
    log(f"  secciones comparadas: {nat['n_secciones']:,}   solo {a.base}: {(m['estado']==f'solo_{a.base}').sum():,}   solo {a.target}: {(m['estado']==f'solo_{a.target}').sum():,}")
    for b in blocs:
        log(f"  {BLOQUE_LABEL.get(b, b):<22} {nat['pct_'+b+f'_{a.base}']:6.2f}% -> {nat['pct_'+b+f'_{a.target}']:6.2f}%  ({nat['d_'+b]:+.2f} pp)")
    log(f"  participación          {nat[f'participacion_{a.base}']:6.2f}% -> {nat[f'participacion_{a.target}']:6.2f}%  ({nat['d_participacion']:+.2f} pp)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
