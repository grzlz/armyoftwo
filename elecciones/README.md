# Delta electoral por sección (INE, diputaciones federales)

Pipeline para ver **cómo cambió el voto entre dos elecciones federales en cada sección
electoral** de México, de cara a la intermedia de 2027. Compara por defecto 2021 → 2024
(misma elección: diputaciones de mayoría relativa, mismas coaliciones), y acepta 2018.

**Sobre el nivel "clave electoral":** el INE no publica resultados por clave de elector
(el voto es secreto). El nivel más fino que existe es la **sección electoral**, identificada
por entidad (2 dígitos) + sección (4 dígitos), p. ej. `09-0123`. Todo aquí se calcula a ese
nivel, sumando las actas de casilla de cada sección.

## Flujo

```
data/raw/<año>/*.zip|*.csv   ──►  build_delta.py  ──►  data/processed/*.csv + dashboard_data.json
                                                            │
                                               make_dashboard.py  ──►  out/delta_secciones.html
```

1. **Conseguir las bases de datos del INE** (una por elección). Son ZIP con un CSV por
   acta/casilla:
   * 2024: https://computos2024.ine.mx → pestaña *Base de datos* → Diputaciones (`DIP_FED_2024.csv`)
   * 2021: https://computos2021.ine.mx/base-de-datos → Diputaciones (`Diputaciones.csv`)
   * 2018: https://computos2018.ine.mx → Base de datos → Diputados

   `python fetch_ine.py --years 2021 2024` intenta descargarlos solos; si la red no llega
   a `*.ine.mx`, descárgalos en el navegador y guárdalos en `data/raw/2021/` y `data/raw/2024/`
   (ZIP o CSV, da igual; el script descomprime).

2. **Agregar a sección y calcular el delta**

   ```
   python build_delta.py                       # 2021 -> 2024
   python build_delta.py --base 2018 --target 2021
   python build_delta.py --file 2021=/ruta/Diputaciones.csv --file 2024=/ruta/DIP_FED_2024.csv
   ```

   Detecta solo el encabezado (las bases traen 1-3 líneas de preámbulo con la fecha de corte),
   el delimitador (`|` o `,`) y la codificación; reconoce las columnas de partido y coalición
   por nombre; descarta las actas de representación proporcional de casillas especiales
   (`TIPO_ACTA` no modal) para no duplicar; y avisa si alguna columna no se reconoce.

   Salidas en `data/processed/`:

   | archivo | contenido |
   |---|---|
   | `secciones_<año>.csv` | por sección: actas, lista nominal, total, nulos, votos por partido/combinación, votos y % por bloque, participación |
   | `delta_<base>_<objetivo>.csv` | las dos elecciones lado a lado y `d_<bloque>` en puntos porcentuales, `d_participacion`, `d_lista_nominal`, `estado` (ambas / solo_<año>) |
   | `resumen_entidad_*.csv`, `resumen_distrito_*.csv` | lo mismo ponderado por votos, por entidad y por distrito federal (distritos del año objetivo) |
   | `dashboard_data.json` | insumo compacto del tablero |

3. **Tablero**: `python make_dashboard.py` genera `out/delta_secciones.html`, un archivo
   autocontenido (ábrelo en el navegador, no necesita servidor). Filtros por entidad,
   distrito, bloque, mínimo de votos y búsqueda de sección; KPIs ponderados; histograma del
   cambio por sección; barras divergentes por entidad o distrito; dispersión año base vs
   objetivo; tablas de mayores ganancias y pérdidas y tabla completa.

## Bloques

Definidos en `BLOQUES` dentro de `build_delta.py`. Una columna de coalición se asigna al
bloque que contiene a **todos** sus partidos, así el bloque suma votos individuales más
todas sus combinaciones.

| año | bloques |
|---|---|
| 2021 y 2024 | Morena + PT + PVEM · PAN + PRI + PRD · MC · Otros (PES, RSP, FXM, independientes) |
| 2018 | Morena + PT + PES · PRI + PVEM + NA · PAN + PRD + MC |

Las coaliciones de 2018 no coinciden con las de 2021/2024, así que al comparar 2018 con
otro año solo se obtiene delta de participación y de "Otros"; los porcentajes por bloque
de cada año sí salen en `secciones_<año>.csv`.

## Decisiones de método

* El porcentaje de un bloque es sobre el **total de votos** de la sección (incluye nulos y
  no registrados), igual que el "porcentaje" de los reportes del INE.
* Participación = total de votos / lista nominal de las casillas computadas.
* Las secciones creadas o suprimidas por el INE entre elecciones (reseccionamiento) quedan
  marcadas con `estado = solo_<año>` y fuera de los deltas.
* Los distritos cambiaron con la redistritación de 2023; los resúmenes por distrito usan los
  distritos del año objetivo.

## Requisitos

Python 3.10+ y `pandas` (`pip install pandas`). Sin otras dependencias.
