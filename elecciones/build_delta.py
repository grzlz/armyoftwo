#!/usr/bin/env python3
"""Carga resultados del INE (diputaciones federales de mayoría relativa) en una base SQLite a nivel
SECCIÓN ELECTORAL y expone el delta entre elecciones como vistas SQL.

Clave de sección = entidad (2 dígitos) + sección (4 dígitos), p. ej. 09-0123. Es el nivel geográfico
más fino con resultados agregados; no existe información por clave de elector (voto secreto).

Formatos de entrada (ambos se descargan con fetch_ine.py):
  * SICEE, sicee.ine.mx: CSV por sección (*_SEC.csv) o por casilla (*_CAS.csv). Fuente por defecto.
  * Cómputos distritales, computosAAAA.ine.mx: CSV por acta (DIP_FED_2024.csv, Diputaciones.csv).

La base acumula años. Cada corrida carga los años pedidos y omite los que ya están cargados con el
mismo archivo (mismo sha256), salvo --force.

Tablas
  fuentes            un renglón por año: archivo, sha256, url, preámbulo, filas leídas e incluidas
  entidades          catálogo de entidades
  bloques            bloques de cada año y sus partidos
  columnas_partido   cada columna de partido o combinación del archivo y el bloque al que suma
  crudo_<año>        el archivo original (columnas normalizadas) + INCLUIDA (1 si entra al agregado)
  secciones          por año y sección: casillas, lista nominal, votos, nulos, no registrados,
                     independientes, participación y dif_cuadre
  votos_seccion      votos por año, sección y columna de partido o combinación (formato largo)
  bloques_seccion    votos y porcentaje por año, sección y bloque
Vistas (cualquier par de años cargados, anio_base < anio_objetivo)
  delta_seccion, delta_participacion, resumen_entidad, resumen_distrito, resumen_nacional

Uso:
    python build_delta.py                              # carga 2021 y 2024 y resume 2021 -> 2024
    python build_delta.py --base 2018 --target 2021
    python build_delta.py --file 2024=/ruta/DIP_FED_2024.csv --force
    python build_delta.py --csv                        # además exporta CSV a data/processed/
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sqlite3
import sys
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DEFAULT_DB = HERE / "data" / "elecciones.sqlite"
SCHEMA_VERSION = 1

for _t in (np.int64, np.int32, np.int16, np.int8):
    sqlite3.register_adapter(_t, int)
sqlite3.register_adapter(np.float64, float)
sqlite3.register_adapter(np.float32, float)
sqlite3.register_adapter(np.bool_, int)

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

# Bloques por año. Una columna de coalición (p. ej. PVEM_PT_MORENA) se asigna al bloque que contiene a
# TODOS sus partidos, así el bloque suma votos individuales + combinaciones. Lo demás va a OTROS.
BLOQUES = {
    2024: {"MORENA_ALIADOS": {"MORENA", "PT", "PVEM"}, "PAN_PRI_PRD": {"PAN", "PRI", "PRD"}, "MC": {"MC"}},
    2021: {"MORENA_ALIADOS": {"MORENA", "PT", "PVEM"}, "PAN_PRI_PRD": {"PAN", "PRI", "PRD"}, "MC": {"MC"}},
    # 2018 tuvo coaliciones distintas (PVEM con PRI, MC con PAN-PRD, PES con Morena).
    2018: {"MORENA_PT_PES": {"MORENA", "PT", "PES"}, "PRI_PVEM_NA": {"PRI", "PVEM", "NA"}, "PAN_PRD_MC": {"PAN", "PRD", "MC"}},
}
BLOQUE_LABEL = {
    "MORENA_ALIADOS": "Morena + PT + PVEM", "PAN_PRI_PRD": "PAN + PRI + PRD", "MC": "MC", "OTROS": "Otros",
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

# ---------------------------------------------------------------- esquema SQLite
SCHEMA = """
CREATE TABLE IF NOT EXISTS entidades (
  entidad_id INTEGER PRIMARY KEY,
  nombre     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fuentes (
  anio            INTEGER PRIMARY KEY,
  archivo         TEXT NOT NULL,
  sha256          TEXT NOT NULL,
  url             TEXT,
  formato         TEXT,             -- sicee_seccion | sicee_casilla | computos_acta
  preambulo       TEXT,
  filas_leidas    INTEGER,
  filas_incluidas INTEGER,
  secciones       INTEGER,
  tabla_cruda     TEXT,
  cargado_en      TEXT
);
CREATE TABLE IF NOT EXISTS bloques (
  anio     INTEGER NOT NULL,
  bloque   TEXT NOT NULL,
  orden    INTEGER NOT NULL,
  etiqueta TEXT NOT NULL,
  partidos TEXT NOT NULL,           -- partidos ordenados, separados por coma; 'OTROS' para el resto
  PRIMARY KEY (anio, bloque)
);
CREATE TABLE IF NOT EXISTS columnas_partido (
  anio     INTEGER NOT NULL,
  columna  TEXT NOT NULL,           -- nombre normalizado de la columna en el archivo del INE
  original TEXT NOT NULL,
  partidos TEXT NOT NULL,
  bloque   TEXT NOT NULL,
  PRIMARY KEY (anio, columna)
);
CREATE TABLE IF NOT EXISTS secciones (
  anio          INTEGER NOT NULL,
  clave         TEXT NOT NULL,      -- EE-SSSS
  entidad_id    INTEGER NOT NULL,
  seccion       INTEGER NOT NULL,
  distrito      INTEGER,            -- distrito federal de ese año
  casillas      INTEGER NOT NULL,
  lista_nominal INTEGER NOT NULL,
  total_votos   INTEGER NOT NULL,
  nulos         INTEGER NOT NULL,
  cnr           INTEGER NOT NULL,   -- candidaturas no registradas
  ci            INTEGER NOT NULL,   -- candidaturas independientes
  participacion REAL,               -- % total_votos / lista_nominal
  dif_cuadre    INTEGER NOT NULL,   -- total_votos - bloques - nulos - cnr; 0 si cuadra
  PRIMARY KEY (anio, clave)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS ix_secciones_clave ON secciones (clave, anio);
CREATE INDEX IF NOT EXISTS ix_secciones_geo   ON secciones (anio, entidad_id, distrito);
CREATE TABLE IF NOT EXISTS votos_seccion (
  anio    INTEGER NOT NULL,
  clave   TEXT NOT NULL,
  columna TEXT NOT NULL,
  votos   INTEGER NOT NULL,
  PRIMARY KEY (anio, clave, columna)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS bloques_seccion (
  anio   INTEGER NOT NULL,
  clave  TEXT NOT NULL,
  bloque TEXT NOT NULL,
  votos  INTEGER NOT NULL,
  pct    REAL,                      -- % sobre total_votos de la sección
  PRIMARY KEY (anio, clave, bloque)
) WITHOUT ROWID;
"""

VIEWS = """
DROP VIEW IF EXISTS resumen_nacional;
DROP VIEW IF EXISTS resumen_distrito;
DROP VIEW IF EXISTS resumen_entidad;
DROP VIEW IF EXISTS delta_participacion;
DROP VIEW IF EXISTS delta_seccion;
DROP VIEW IF EXISTS bloques_comparables;

-- Bloques con la misma composición en dos años (comparables entre sí).
CREATE VIEW bloques_comparables AS
SELECT a.anio AS anio_base, b.anio AS anio_objetivo, b.bloque, b.etiqueta, b.orden
FROM bloques a
JOIN bloques b ON b.bloque = a.bloque AND b.partidos = a.partidos AND b.anio > a.anio;

-- Cambio por sección y bloque. Solo secciones presentes en ambos años.
CREATE VIEW delta_seccion AS
SELECT p.anio_base, p.anio_objetivo, sa.clave, sa.entidad_id, e.nombre AS entidad, sa.seccion,
       sb.distrito AS distrito_objetivo, p.bloque, p.etiqueta, p.orden,
       sa.total_votos AS total_base, sb.total_votos AS total_objetivo,
       ba.votos AS votos_base, bb.votos AS votos_objetivo,
       ba.pct AS pct_base, bb.pct AS pct_objetivo,
       ROUND(bb.pct - ba.pct, 3) AS d_pp
FROM bloques_comparables p
JOIN secciones sa       ON sa.anio = p.anio_base
JOIN secciones sb       ON sb.anio = p.anio_objetivo AND sb.clave = sa.clave
JOIN bloques_seccion ba ON ba.anio = p.anio_base     AND ba.clave = sa.clave AND ba.bloque = p.bloque
JOIN bloques_seccion bb ON bb.anio = p.anio_objetivo AND bb.clave = sa.clave AND bb.bloque = p.bloque
LEFT JOIN entidades e   ON e.entidad_id = sa.entidad_id;

-- Cambio de participación y lista nominal por sección.
CREATE VIEW delta_participacion AS
SELECT sa.anio AS anio_base, sb.anio AS anio_objetivo, sa.clave, sa.entidad_id, e.nombre AS entidad,
       sa.seccion, sb.distrito AS distrito_objetivo,
       sa.lista_nominal AS ln_base, sb.lista_nominal AS ln_objetivo,
       sa.total_votos AS total_base, sb.total_votos AS total_objetivo,
       sa.participacion AS part_base, sb.participacion AS part_objetivo,
       ROUND(sb.participacion - sa.participacion, 3) AS d_pp
FROM secciones sa
JOIN secciones sb     ON sb.clave = sa.clave AND sb.anio > sa.anio
LEFT JOIN entidades e ON e.entidad_id = sa.entidad_id;

-- Resúmenes ponderados por votos (no promedio de porcentajes).
CREATE VIEW resumen_entidad AS
WITH p AS (
  SELECT anio_base, anio_objetivo, entidad_id,
         100.0 * SUM(total_base)     / NULLIF(SUM(ln_base), 0)     AS part_base,
         100.0 * SUM(total_objetivo) / NULLIF(SUM(ln_objetivo), 0) AS part_objetivo
  FROM delta_participacion GROUP BY anio_base, anio_objetivo, entidad_id)
SELECT d.anio_base, d.anio_objetivo, d.entidad_id, d.entidad, d.bloque, d.etiqueta, d.orden,
       COUNT(*) AS secciones,
       ROUND(100.0 * SUM(d.votos_base)     / NULLIF(SUM(d.total_base), 0), 3)     AS pct_base,
       ROUND(100.0 * SUM(d.votos_objetivo) / NULLIF(SUM(d.total_objetivo), 0), 3) AS pct_objetivo,
       ROUND(100.0 * SUM(d.votos_objetivo) / NULLIF(SUM(d.total_objetivo), 0)
           - 100.0 * SUM(d.votos_base)     / NULLIF(SUM(d.total_base), 0), 3)     AS d_pp,
       ROUND(p.part_base, 3) AS part_base, ROUND(p.part_objetivo, 3) AS part_objetivo,
       ROUND(p.part_objetivo - p.part_base, 3) AS d_participacion
FROM delta_seccion d
JOIN p ON p.anio_base = d.anio_base AND p.anio_objetivo = d.anio_objetivo AND p.entidad_id = d.entidad_id
GROUP BY d.anio_base, d.anio_objetivo, d.entidad_id, d.bloque;

CREATE VIEW resumen_distrito AS
WITH p AS (
  SELECT anio_base, anio_objetivo, entidad_id, distrito_objetivo,
         100.0 * SUM(total_base)     / NULLIF(SUM(ln_base), 0)     AS part_base,
         100.0 * SUM(total_objetivo) / NULLIF(SUM(ln_objetivo), 0) AS part_objetivo
  FROM delta_participacion GROUP BY anio_base, anio_objetivo, entidad_id, distrito_objetivo)
SELECT d.anio_base, d.anio_objetivo, d.entidad_id, d.entidad, d.distrito_objetivo, d.bloque, d.etiqueta, d.orden,
       COUNT(*) AS secciones,
       ROUND(100.0 * SUM(d.votos_base)     / NULLIF(SUM(d.total_base), 0), 3)     AS pct_base,
       ROUND(100.0 * SUM(d.votos_objetivo) / NULLIF(SUM(d.total_objetivo), 0), 3) AS pct_objetivo,
       ROUND(100.0 * SUM(d.votos_objetivo) / NULLIF(SUM(d.total_objetivo), 0)
           - 100.0 * SUM(d.votos_base)     / NULLIF(SUM(d.total_base), 0), 3)     AS d_pp,
       ROUND(p.part_base, 3) AS part_base, ROUND(p.part_objetivo, 3) AS part_objetivo,
       ROUND(p.part_objetivo - p.part_base, 3) AS d_participacion
FROM delta_seccion d
JOIN p ON p.anio_base = d.anio_base AND p.anio_objetivo = d.anio_objetivo
      AND p.entidad_id = d.entidad_id AND p.distrito_objetivo IS d.distrito_objetivo
GROUP BY d.anio_base, d.anio_objetivo, d.entidad_id, d.distrito_objetivo, d.bloque;

CREATE VIEW resumen_nacional AS
WITH p AS (
  SELECT anio_base, anio_objetivo,
         100.0 * SUM(total_base)     / NULLIF(SUM(ln_base), 0)     AS part_base,
         100.0 * SUM(total_objetivo) / NULLIF(SUM(ln_objetivo), 0) AS part_objetivo
  FROM delta_participacion GROUP BY anio_base, anio_objetivo)
SELECT d.anio_base, d.anio_objetivo, d.bloque, d.etiqueta, d.orden,
       COUNT(*) AS secciones,
       ROUND(100.0 * SUM(d.votos_base)     / NULLIF(SUM(d.total_base), 0), 3)     AS pct_base,
       ROUND(100.0 * SUM(d.votos_objetivo) / NULLIF(SUM(d.total_objetivo), 0), 3) AS pct_objetivo,
       ROUND(100.0 * SUM(d.votos_objetivo) / NULLIF(SUM(d.total_objetivo), 0)
           - 100.0 * SUM(d.votos_base)     / NULLIF(SUM(d.total_base), 0), 3)     AS d_pp,
       ROUND(p.part_base, 3) AS part_base, ROUND(p.part_objetivo, 3) AS part_objetivo,
       ROUND(p.part_objetivo - p.part_base, 3) AS d_participacion
FROM delta_seccion d
JOIN p ON p.anio_base = d.anio_base AND p.anio_objetivo = d.anio_objetivo
GROUP BY d.anio_base, d.anio_objetivo, d.bloque;
"""


# ---------------------------------------------------------------- utilidades
def norm(s: object) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s.upper()).strip("_")
    for long, short in MULTIWORD:
        s = s.replace(long, short)
    return s


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def unzip_all(raw: Path) -> None:
    """Descomprime cada ZIP junto a sí mismo, incluidos ZIP anidados (cómputos 2024 trae uno por elección)."""
    while True:
        pending = [z for z in raw.rglob("*.zip") if not z.with_suffix("").exists()]
        if not pending:
            return
        for z in pending:
            log(f"descomprimiendo {z.relative_to(raw)}")
            try:
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(z.with_suffix(""))
            except zipfile.BadZipFile:
                log(f"  {z.name} no es un ZIP válido; lo ignoro")
                z.with_suffix("").mkdir(exist_ok=True)


def year_of(p: Path) -> int | None:
    for part in [p.name, *[q.name for q in p.parents]]:
        m = re.search(r"(?<!\d)((?:19|20)\d\d)", part)
        if m:
            return int(m.group(1))
    return None


def file_kind(p: Path) -> tuple[int, str] | None:
    """(prioridad, formato) de un CSV de diputaciones federales MR, o None si no aplica."""
    if p.suffix.lower() not in (".csv", ".txt"):
        return None
    n = norm(p.stem)
    toks = n.split("_")
    if "DIP" not in n or "CAND" in n:
        return None
    if set(toks) & {"LEEME", "README", "RP", "LOC", "LOCAL", "LOCALES", "CATALOGO"}:
        return None
    last = toks[-1]
    if last in {"ENT", "DIS", "DIST", "MUN", "MUNI", "CIR", "CIRC"}:
        return None
    if last in {"SEC", "SECC"}:
        return 3, "sicee_seccion"
    if last in {"CAS", "CASILLA"}:
        return 1, "sicee_casilla"
    return 2, "computos_acta"


def discover(raw: Path) -> dict[int, tuple[Path, str]]:
    """Elige por año el mejor CSV: SICEE por sección > cómputos por acta > SICEE por casilla."""
    found: dict[int, list[tuple[int, int, Path, str]]] = {}
    for p in raw.rglob("*"):
        k = file_kind(p)
        y = year_of(p) if k else None
        if k and y:
            found.setdefault(y, []).append((k[0], p.stat().st_size, p, k[1]))
    out = {}
    for y, cands in found.items():
        cands.sort(key=lambda t: (t[0], t[1]), reverse=True)
        out[y] = (cands[0][2], cands[0][3])
        if len(cands) > 1:
            log(f"[{y}] uso {cands[0][2]} ({cands[0][3]}); también hay: {[str(c[2]) for c in cands[1:]]}")
    return out


def sniff(path: Path) -> tuple[str, int, str]:
    """Devuelve (encoding, índice de la línea de encabezado, delimitador)."""
    data = path.read_bytes()[:200_000]
    try:
        text, enc = data.decode("utf-8-sig"), "utf-8-sig"
    except UnicodeDecodeError:
        text, enc = data.decode("latin-1"), "latin-1"
    for i, line in enumerate(text.splitlines()[:60]):
        if "SECCION" in norm(line):
            counts = {d: line.count(d) for d in ("|", ",", ";", "\t")}
            delim = max(counts, key=counts.get)
            if counts[delim] >= 5:
                return enc, i, delim
    raise SystemExit(f"{path}: no encontré una línea de encabezado con SECCION en las primeras 60 líneas")


def read_source(path: Path) -> tuple[pd.DataFrame, str]:
    enc, hdr, delim = sniff(path)
    preamble = ""
    if hdr > 0:
        with open(path, encoding=enc, errors="replace") as f:
            preamble = " / ".join(next(f).strip() for _ in range(hdr)).strip(" /")
    log(f"leyendo {path.name}: encoding={enc} encabezado=línea {hdr + 1} delim={delim!r}")
    df = pd.read_csv(path, sep=delim, skiprows=hdr, encoding=enc, dtype=str, on_bad_lines="warn", low_memory=False)
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
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
        elif n in ("CASILLAS", "NUM_CASILLAS", "TOTAL_CASILLAS"):
            roles["casillas"] = c
        elif n.startswith("LISTA_NOMINAL"):
            roles.setdefault("ln", c)
        elif n in ("TOTAL_VOTOS_CALCULADOS", "TOTAL_VOTOS_CALCULADO"):
            roles["total"] = c
        elif n.startswith("TOTAL_VOTOS"):
            roles.setdefault("total_alt", c)
        elif "NO_REGISTRAD" in n or "NREG" in n:
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


def unique_names(cols: list[str]) -> dict[str, str]:
    """Nombre normalizado y único (apto para SQL) de cada columna original."""
    out, used = {}, set()
    for c in cols:
        n = norm(c) or "COL"
        if n[0].isdigit():
            n = "C_" + n
        k, i = n, 2
        while k in used:
            k, i = f"{n}_{i}", i + 1
        used.add(k)
        out[c] = k
    return out


def typed_raw(df: pd.DataFrame, names: dict[str, str], incl: pd.Series) -> pd.DataFrame:
    """Copia del archivo original con columnas numéricas como enteros; claves con ceros a la izquierda quedan como texto."""
    raw = {}
    for c in df.columns:
        st = df[c].fillna("").astype(str).str.strip()
        nonempty = st != ""
        num = pd.to_numeric(st.where(nonempty).str.replace(",", "", regex=False), errors="coerce")
        lead0 = st.str.match(r"^-?0\d").any()
        if nonempty.any() and num[nonempty].notna().all() and not lead0:
            raw[names[c]] = num.round().astype("Int64") if (num.dropna() % 1 == 0).all() else num
        else:
            raw[names[c]] = df[c]
    out = pd.DataFrame(raw, index=df.index)
    out["INCLUIDA"] = incl.astype(int).to_numpy()
    return out


# ---------------------------------------------------------------- agregación por sección
def aggregate(path: Path, year: int, fmt: str) -> dict:
    if year not in BLOQUES:
        raise SystemExit(f"[{year}] define BLOQUES[{year}] en build_delta.py (coaliciones de ese año)")
    df, preamble = read_source(path)
    roles, party, ci, unknown = classify(list(df.columns))
    if "ent_id" not in roles and "ent_name" in roles and to_num(df[roles["ent_name"]]).gt(0).all():
        roles["ent_id"] = roles["ent_name"]
    missing = [r for r in ("ent_id", "seccion", "total") if r not in roles]
    if missing:
        raise SystemExit(f"[{year}] faltan columnas clave {missing}. Columnas vistas: {list(df.columns)}")
    if not party:
        raise SystemExit(f"[{year}] no reconocí columnas de partido. Columnas: {list(df.columns)}")
    log(f"[{year}] partidos/coaliciones: {list(party)}")
    if unknown:
        log(f"[{year}] columnas ignoradas: {unknown}")
    for c in [*party, *ci, roles["total"]]:
        st = df[c].fillna("").astype(str).str.strip()
        bad = (st != "") & pd.to_numeric(st.str.replace(",", "", regex=False), errors="coerce").isna()
        if bad.any():
            log(f"[{year}] aviso: {int(bad.sum()):,} valores no numéricos en {c!r} (cuentan como 0), p. ej. {st[bad].iloc[0]!r}")

    n0 = len(df)
    incl = pd.Series(True, index=df.index)
    # Una sola acta por casilla: en cómputos de diputaciones las casillas especiales traen acta MR y RP.
    if "tipo_acta" in roles:
        vc = df[roles["tipo_acta"]].value_counts(dropna=False)
        if len(vc) > 1:
            rest = vc.iloc[1:].sum()
            if rest / n0 <= 0.05:
                incl &= df[roles["tipo_acta"]] == vc.index[0]
                log(f"[{year}] TIPO_ACTA: conservo {vc.index[0]!r} ({vc.iloc[0]:,} actas), descarto {rest:,} de otros tipos {dict(vc.iloc[1:])}")
            else:
                log(f"[{year}] TIPO_ACTA con varios valores grandes {dict(vc)}; conservo todas (revisa duplicidad MR/RP)")

    ent = to_num(df[roles["ent_id"]]).astype(int)
    sec = to_num(df[roles["seccion"]]).astype(int)
    valid = (ent > 0) & (sec > 0)
    if (incl & ~valid).any():
        log(f"[{year}] descarto {int((incl & ~valid).sum()):,} filas sin entidad/sección válida (totales o pies de página)")
    incl &= valid
    d = df[incl]

    def col(role: str, default: float = 0):
        return to_num(d[roles[role]]).to_numpy() if role in roles else default

    out = pd.DataFrame({"entidad_id": ent[incl].to_numpy(), "seccion": sec[incl].to_numpy()})
    out["distrito"] = col("dist_id")
    out["casillas"] = col("casillas", 1)
    out["lista_nominal"] = col("ln")
    out["total_votos"] = col("total")
    out["nulos"] = col("nulos")
    out["cnr"] = col("cnr")
    out["ci"] = sum((to_num(d[c]).to_numpy() for c in ci), start=np.zeros(len(d)))
    pnames = unique_names(list(party))
    for c, n in pnames.items():
        out["v_" + n] = to_num(d[c]).to_numpy()

    agg = {c: "sum" for c in out.columns if c not in ("entidad_id", "seccion", "distrito")}
    agg["distrito"] = "max"
    g = out.groupby(["entidad_id", "seccion"], as_index=False).agg(agg)
    for c in g.columns:
        g[c] = g[c].round().astype("int64")
    g["clave"] = g["entidad_id"].map("{:02d}".format) + "-" + g["seccion"].map("{:04d}".format)

    blocs = BLOQUES[year]
    col_bloc = {c: next((b for b, m in blocs.items() if set(parts) <= m), "OTROS") for c, parts in party.items()}
    bloc_votes: dict[str, pd.Series] = {}
    for b in [*blocs, "OTROS"]:
        cols = ["v_" + pnames[c] for c in party if col_bloc[c] == b]
        bloc_votes[b] = g[cols].sum(axis=1) if cols else pd.Series(0, index=g.index, dtype="int64")
        log(f"[{year}] bloque {b}: {[c[2:] for c in cols]}" + (" + independientes" if b == "OTROS" else ""))
    bloc_votes["OTROS"] = bloc_votes["OTROS"] + g["ci"]

    g["dif_cuadre"] = g["total_votos"] - sum(bloc_votes.values()) - g["nulos"] - g["cnr"]
    nbad = int((g["dif_cuadre"] != 0).sum())
    if nbad:
        log(f"[{year}] aviso: en {nbad:,} de {len(g):,} secciones bloques+nulos+no registrados no suman TOTAL_VOTOS "
            f"(dif. absoluta media {g['dif_cuadre'].abs().mean():.2f}); revisa columnas_partido y secciones.dif_cuadre")
    tot = g["total_votos"].where(g["total_votos"] > 0)
    g["participacion"] = (g["total_votos"] / g["lista_nominal"].where(g["lista_nominal"] > 0) * 100).round(3)
    secciones = g[["clave", "entidad_id", "seccion", "distrito", "casillas", "lista_nominal", "total_votos",
                   "nulos", "cnr", "ci", "participacion", "dif_cuadre"]].copy()
    secciones["distrito"] = secciones["distrito"].where(secciones["distrito"] > 0)

    vcols = ["v_" + n for n in pnames.values()]
    votos = g.melt(id_vars="clave", value_vars=vcols, var_name="columna", value_name="votos")
    votos["columna"] = votos["columna"].str[2:]
    bloques_sec = pd.concat([pd.DataFrame({"clave": g["clave"], "bloque": b, "votos": v, "pct": (v / tot * 100).round(3)})
                             for b, v in bloc_votes.items()], ignore_index=True)
    bloques_def = pd.DataFrame(
        [(b, i, BLOQUE_LABEL.get(b, b), ",".join(sorted(m))) for i, (b, m) in enumerate(blocs.items())]
        + [("OTROS", len(blocs), BLOQUE_LABEL["OTROS"], "OTROS")],
        columns=["bloque", "orden", "etiqueta", "partidos"])
    columnas = pd.DataFrame([(pnames[c], c, ",".join(party[c]), col_bloc[c]) for c in party],
                            columns=["columna", "original", "partidos", "bloque"])
    return {"secciones": secciones, "votos": votos, "bloques_sec": bloques_sec, "bloques": bloques_def,
            "columnas": columnas, "raw": typed_raw(df, unique_names(list(df.columns)), incl),
            "preamble": preamble, "rows_in": n0, "rows_incl": int(incl.sum()), "fmt": fmt}


# ---------------------------------------------------------------- SQLite
def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    v = con.execute("PRAGMA user_version").fetchone()[0]
    if v not in (0, SCHEMA_VERSION):
        raise SystemExit(f"{path} tiene esquema v{v}; este script usa v{SCHEMA_VERSION}. Usa otra --db o bórrala.")
    con.executescript(SCHEMA)
    con.executescript(VIEWS)
    con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    con.executemany("INSERT OR REPLACE INTO entidades VALUES (?, ?)", ENTIDADES.items())
    con.commit()
    return con


def insert_df(con: sqlite3.Connection, table: str, df: pd.DataFrame, year: int) -> None:
    df = df.copy()
    df.insert(0, "anio", year)
    cols = list(df.columns)
    rows = df.astype(object).where(df.notna(), None).itertuples(index=False, name=None)
    con.executemany(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", rows)


def url_for(sha: str, raw_dir: Path, path: Path) -> str | None:
    """Busca la URL de descarga en el manifiesto de fetch_ine.py (por sha256 del CSV o del ZIP que lo contiene)."""
    man = raw_dir / "descargas.csv"
    if not man.exists():
        return None
    rows = list(csv.DictReader(open(man, encoding="utf-8")))
    for r in rows:
        if r.get("sha256") == sha:
            return r.get("url")
    for parent in path.resolve().parents:  # CSV extraído de un ZIP descargado: data/raw/2024/X.zip -> data/raw/2024/X/...
        for r in rows:
            if r.get("archivo") and Path(r["archivo"]).resolve().with_suffix("") == parent:
                return r.get("url")
    return None


def load_year(con: sqlite3.Connection, year: int, path: Path, fmt: str, raw_dir: Path, force: bool) -> bool:
    sha = sha256_of(path)
    prev = con.execute("SELECT sha256 FROM fuentes WHERE anio = ?", (year,)).fetchone()
    if prev and prev[0] == sha and not force:
        log(f"[{year}] {path.name} ya está en la base (mismo sha256); lo omito. Usa --force para recargar.")
        return False
    r = aggregate(path, year, fmt)
    table = f"crudo_{year}"
    with con:  # si algo falla a medio camino, el año queda sin fuente y la siguiente corrida lo recarga
        con.execute("DELETE FROM fuentes WHERE anio = ?", (year,))
    con.execute(f'DROP TABLE IF EXISTS "{table}"')
    r["raw"].to_sql(table, con, index=False, chunksize=20_000)
    with con:
        for t in ("bloques", "columnas_partido", "secciones", "votos_seccion", "bloques_seccion"):
            con.execute(f"DELETE FROM {t} WHERE anio = ?", (year,))
        insert_df(con, "bloques", r["bloques"], year)
        insert_df(con, "columnas_partido", r["columnas"], year)
        insert_df(con, "secciones", r["secciones"], year)
        insert_df(con, "votos_seccion", r["votos"], year)
        insert_df(con, "bloques_seccion", r["bloques_sec"], year)
        con.execute(
            "INSERT INTO fuentes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (year, path.name, sha, url_for(sha, raw_dir, path), fmt, r["preamble"], r["rows_in"], r["rows_incl"],
             len(r["secciones"]), table, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")))
    s = r["secciones"]
    log(f"[{year}] cargado: {len(s):,} secciones, {int(s['total_votos'].sum()):,} votos, LN {int(s['lista_nominal'].sum()):,}; "
        f"crudo en {table} ({r['rows_in']:,} filas, {r['rows_incl']:,} incluidas)")
    return True


def summary(con: sqlite3.Connection, base: int, target: int) -> None:
    only = lambda a, b: con.execute(  # noqa: E731
        "SELECT COUNT(*) FROM secciones s WHERE s.anio = ? AND NOT EXISTS "
        "(SELECT 1 FROM secciones t WHERE t.anio = ? AND t.clave = s.clave)", (a, b)).fetchone()[0]
    rows = con.execute(
        "SELECT etiqueta, secciones, pct_base, pct_objetivo, d_pp, part_base, part_objetivo, d_participacion "
        "FROM resumen_nacional WHERE anio_base = ? AND anio_objetivo = ? ORDER BY orden", (base, target)).fetchall()
    log(f"\nResumen nacional {base} -> {target} (secciones presentes en ambas elecciones):")
    if not rows:
        log("  no hay bloques comparables entre esos años")
        return
    log(f"  secciones comparadas: {rows[0][1]:,}   solo {base}: {only(base, target):,}   solo {target}: {only(target, base):,}")
    for et, _, pa, pb, dd, *_ in rows:
        log(f"  {et:<22} {pa:6.2f}% -> {pb:6.2f}%  ({dd:+.2f} pp)")
    _, _, _, _, _, qa, qb, dq = rows[0]
    log(f"  {'participación':<22} {qa:6.2f}% -> {qb:6.2f}%  ({dq:+.2f} pp)")


def export_csv(con: sqlite3.Connection, base: int, target: int, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    pair = (base, target)
    jobs = [
        (f"delta_seccion_{base}_{target}.csv", "SELECT * FROM delta_seccion WHERE anio_base=? AND anio_objetivo=? ORDER BY clave, orden", pair),
        (f"delta_participacion_{base}_{target}.csv", "SELECT * FROM delta_participacion WHERE anio_base=? AND anio_objetivo=? ORDER BY clave", pair),
        (f"resumen_entidad_{base}_{target}.csv", "SELECT * FROM resumen_entidad WHERE anio_base=? AND anio_objetivo=? ORDER BY entidad_id, orden", pair),
        (f"resumen_distrito_{base}_{target}.csv", "SELECT * FROM resumen_distrito WHERE anio_base=? AND anio_objetivo=? ORDER BY entidad_id, distrito_objetivo, orden", pair),
        (f"secciones_{base}.csv", "SELECT * FROM secciones WHERE anio=? ORDER BY clave", (base,)),
        (f"secciones_{target}.csv", "SELECT * FROM secciones WHERE anio=? ORDER BY clave", (target,)),
    ]
    for name, sql, params in jobs:
        pd.read_sql_query(sql, con, params=params).to_csv(out / name, index=False)
    log(f"exporté {len(jobs)} CSV a {out}")


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DEFAULT_DB), help="archivo SQLite (se crea si no existe)")
    ap.add_argument("--raw", default=str(HERE / "data" / "raw"))
    ap.add_argument("--base", type=int, default=2021)
    ap.add_argument("--target", type=int, default=2024)
    ap.add_argument("--file", action="append", default=[], metavar="AÑO=RUTA", help="CSV explícito por año (repetible)")
    ap.add_argument("--force", action="store_true", help="recarga aunque el archivo ya esté en la base")
    ap.add_argument("--csv", nargs="?", const=str(HERE / "data" / "processed"), metavar="DIR",
                    help="exporta además las vistas del par base/objetivo a CSV")
    a = ap.parse_args()
    raw, db = Path(a.raw), Path(a.db)

    files: dict[int, tuple[Path, str]] = {}
    if raw.exists():
        unzip_all(raw)
        files.update(discover(raw))
    for spec in a.file:
        y, p = spec.split("=", 1)
        files[int(y)] = (Path(p), (file_kind(Path(p)) or (0, "computos_acta"))[1])

    con = connect(db)
    loaded = {r[0] for r in con.execute("SELECT anio FROM fuentes")}
    changed = False
    for y in sorted({a.base, a.target}):
        if y in files:
            changed |= load_year(con, y, *files[y], raw, a.force)
        elif y in loaded:
            log(f"[{y}] no hay archivo en {raw}; uso lo que ya está en {db.name}")
        else:
            log(f"no hay datos de {y}: ni archivo en {raw} ni carga previa en {db}. "
                f"Descárgalo con fetch_ine.py --years {y} o pásalo con --file {y}=ruta.csv")
            return 2
    if changed:
        con.execute("ANALYZE")
        con.execute("VACUUM")
    summary(con, a.base, a.target)
    if a.csv:
        export_csv(con, a.base, a.target, Path(a.csv))
    log(f"\nbase: {db} ({db.stat().st_size / 1e6:.1f} MB). Años cargados: {[r[0] for r in con.execute('SELECT anio FROM fuentes ORDER BY anio')]}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
