# Delta electoral por sección (INE, diputaciones federales)

Pipeline para ver **cómo cambió el voto entre dos elecciones federales en cada sección electoral** de
México, de cara a la intermedia de 2027. Descarga los resultados del INE por código, los guarda en una
base **SQLite** y genera un tablero HTML. Compara por defecto 2021 → 2024 (diputaciones de mayoría
relativa, mismas coaliciones) y acepta 2018.

**Sobre el nivel "clave electoral":** el INE no publica resultados por clave de elector (el voto es
secreto). El nivel más fino es la **sección electoral** (entidad de 2 dígitos + sección de 4, p. ej.
`09-0123`), y debajo de ella la casilla. Los agregados están por sección; el detalle por casilla o acta
queda en las tablas `crudo_<año>` cuando la fuente lo trae.

## Flujo

```
fetch_ine.py ──► data/raw/<año>/*.zip ──► build_delta.py ──► data/elecciones.sqlite ──► make_dashboard.py ──► out/delta_secciones.html
 (API SICEE)                                                   tablas + vistas SQL
```

```
pip install pandas
python fetch_ine.py                 # descarga 2021 y 2024 del SICEE
python build_delta.py               # carga a SQLite y muestra el resumen nacional
python make_dashboard.py            # tablero autocontenido
python tests/test_pipeline.py       # prueba de punta a punta sin red (API simulado, datos sintéticos)
```

## 1. Descarga programática del INE (`fetch_ine.py`)

La fuente por defecto es el **SICEE** (Sistema de Consulta de la Estadística de las Elecciones,
sicee.ine.mx), con resultados federales de 1991 a 2024. El sitio es una app web que primero pide la
lista de archivos a un API JSON y luego baja ZIP estáticos. El script hace lo mismo:

```
POST https://sicee-api.ine.mx/api/v1/local/downloads/getCargosElecciones   {"tipo": "FEDERALES_", "anio": 2024}
GET  https://sicee.ine.mx/ACTASSICEEN2024/download/FEDERALES_2024/<ruta_zip>
```

Cada ZIP trae CSV por entidad (`_ENT`), distrito (`_DIS`), municipio (`_MUN`), sección (`_SEC`) y
casilla (`_CAS`). El INE no documenta este API; los endpoints salen del propio sitio y de
[ManuelCadena/inteligencia-electoral-mexico](https://github.com/ManuelCadena/inteligencia-electoral-mexico)
(`scripts/download_sicee.py`). Si cambian, pásalos con `--api` y `--descarga`.

```
python fetch_ine.py --years 2018 2021 2024
python fetch_ine.py --years 2024 --listar              # qué archivos ofrece el INE ese año
python fetch_ine.py --years 2024 --cargo PRESIDENCIA   # otro cargo (por defecto DIPUTACIONES_FED_MR)
python fetch_ine.py --fuente computos --years 2024     # respaldo: página "Base de datos" de computos2024.ine.mx
python fetch_ine.py --url https://.../archivo.zip --year 2024
```

Las descargas quedan en `data/raw/<año>/` y se anotan en `data/raw/descargas.csv` (URL, sha256, fecha).
Reintenta errores de red con espera de 2, 4, 8 y 16 s, valida que el ZIP sea legible y no vuelve a bajar
lo que ya existe (salvo `--force`). También puedes bajar los ZIP en el navegador y dejarlos en
`data/raw/<año>/`.

## 2. Carga a SQLite (`build_delta.py`)

```
python build_delta.py                              # carga 2021 y 2024, resume 2021 -> 2024
python build_delta.py --base 2018 --target 2021    # agrega 2018 a la misma base
python build_delta.py --file 2024=/ruta/DIP_FED_2024.csv --force
python build_delta.py --csv                        # además exporta las vistas a data/processed/*.csv
```

Acepta los CSV del SICEE por sección (preferido) o por casilla, y los de Cómputos Distritales por acta
(`DIP_FED_2024.csv`, `Diputaciones.csv`). Si en `data/raw` hay varios para un año, usa sección > acta >
casilla. Descomprime ZIP (incluso anidados), detecta encabezado, delimitador y codificación, reconoce las
columnas de partido y coalición por nombre y avisa de las que no reconoce. En cómputos descarta las actas
de representación proporcional de casillas especiales para no duplicar votos.

La base acumula años. Una corrida omite un año ya cargado con el mismo archivo (mismo sha256), así que
volver a correrla es barato. La base va en `.gitignore` por tamaño; los ZIP del INE la regeneran.

### Esquema

| tabla | contenido |
|---|---|
| `fuentes` | un renglón por año: archivo, sha256, URL de origen, formato, filas leídas e incluidas |
| `entidades` | catálogo de las 32 entidades |
| `bloques` | bloques de cada año y sus partidos |
| `columnas_partido` | cada columna de partido o combinación del archivo y el bloque al que suma |
| `crudo_<año>` | el archivo del INE tal cual (columnas normalizadas) + `INCLUIDA` (1 si entra al agregado) |
| `secciones` | por año y sección: distrito, casillas, lista nominal, votos, nulos, no registrados, independientes, participación, `dif_cuadre` |
| `votos_seccion` | votos por año, sección y columna de partido o combinación (formato largo) |
| `bloques_seccion` | votos y porcentaje por año, sección y bloque |

| vista | contenido (cualquier par de años cargados, `anio_base < anio_objetivo`) |
|---|---|
| `delta_seccion` | porcentaje de cada bloque en ambos años y `d_pp` por sección |
| `delta_participacion` | lista nominal, votos y participación en ambos años por sección |
| `resumen_entidad`, `resumen_distrito`, `resumen_nacional` | lo mismo ponderado por votos, más participación |

`dif_cuadre` es total de votos menos bloques, nulos y no registrados. Debe ser 0; si no, falta mapear una
columna de partido (revisa `columnas_partido` y el aviso de columnas ignoradas).

### Consultas de ejemplo

```sql
-- Secciones de Nuevo León donde Morena y aliados más crecieron de 2021 a 2024
SELECT clave, distrito_objetivo, pct_base, pct_objetivo, d_pp, total_objetivo
FROM delta_seccion
WHERE anio_base = 2021 AND anio_objetivo = 2024 AND bloque = 'MORENA_ALIADOS'
  AND entidad_id = 19 AND total_base >= 100
ORDER BY d_pp DESC LIMIT 20;

-- Distritos donde cayó la participación
SELECT entidad, distrito_objetivo, part_base, part_objetivo, d_participacion
FROM resumen_distrito
WHERE anio_base = 2021 AND anio_objetivo = 2024 AND bloque = 'MC'
ORDER BY d_participacion LIMIT 15;

-- Secciones que existen en un año y no en el otro (reseccionamiento)
SELECT s.anio, s.clave FROM secciones s
WHERE NOT EXISTS (SELECT 1 FROM secciones t WHERE t.clave = s.clave AND t.anio <> s.anio);

-- Detalle por casilla de una sección (fuente de cómputos o SICEE _CAS)
SELECT * FROM crudo_2024 WHERE SECCION = 123 AND INCLUIDA = 1;
```

```
sqlite3 data/elecciones.sqlite
```

## 3. Tablero (`make_dashboard.py`)

`python make_dashboard.py [--base 2021 --target 2024]` lee la base y escribe `out/delta_secciones.html`,
un archivo autocontenido que se abre en el navegador sin servidor. Filtros por entidad, distrito, bloque,
mínimo de votos y búsqueda de sección; KPIs ponderados; histograma del cambio por sección; barras
divergentes por entidad o distrito; dispersión año base contra objetivo; tablas de mayores ganancias y
pérdidas y tabla completa.

## Bloques

Definidos en `BLOQUES` dentro de `build_delta.py`. Una columna de coalición se asigna al bloque que
contiene a **todos** sus partidos, así el bloque suma votos individuales más todas sus combinaciones.

| año | bloques |
|---|---|
| 2021 y 2024 | Morena + PT + PVEM · PAN + PRI + PRD · MC · Otros (PES, RSP, FXM, independientes) |
| 2018 | Morena + PT + PES · PRI + PVEM + NA · PAN + PRD + MC |

Solo se comparan bloques con la misma composición en ambos años (vista `bloques_comparables`). Entre
2018 y 2021 eso deja solo participación y "Otros"; los porcentajes de cada año sí quedan en
`bloques_seccion`. Para otro año, agrega su entrada a `BLOQUES`.

## Decisiones de método

* El porcentaje de un bloque es sobre el **total de votos** de la sección (incluye nulos y no
  registrados), igual que el "porcentaje" de los reportes del INE.
* Participación = total de votos / lista nominal.
* Las secciones creadas o suprimidas por el INE entre elecciones quedan fuera de los deltas.
* Los distritos cambiaron con la redistritación de 2023; los resúmenes por distrito usan los del año
  objetivo.

## Requisitos

Python 3.10+ y `pandas`. SQLite viene con Python.
