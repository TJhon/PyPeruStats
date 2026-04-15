# Examples

Practical recipes for common MEF data extraction tasks.

---

## Example 1 — Local Government Spending by Department

Drill down from total → local governments → generic category → department. Filters to two generic categories and two departments.

```python
from perustats.MEF import MEFScraper
from perustats.MEF.constants import buttons as BTN
from perustats.MEF.steps.click import ClickBtn, Rows

steps = [
    Rows(["total"]),
    ClickBtn(BTN.NIVEL_GOBIERNO),
    Rows(["locales"]),
    ClickBtn(BTN.GOB_LOCALES_MANCOMUNIDADES, as_column=False),
    Rows(["municipal"]),
    ClickBtn(BTN.GENERICA),
    Rows(["deuda publica", "bienes y servicios"]),
    ClickBtn(BTN.DEPARTAMENTO),
    Rows(["ancash", "lima"]),
    ClickBtn(BTN.MUNICIPALIDAD),
]

df = MEFScraper(steps, convert_numeric=False).run(2020).result
print(df)
```

---

## Example 2 — All Local Governments by Department (no sub-filter)

Use `Rows()` with no arguments to iterate over every row — useful when you don't know what values are present.

```python
steps = [
    Rows(["total"]),
    ClickBtn(BTN.NIVEL_GOBIERNO),
    Rows(["locales"]),
    ClickBtn(BTN.GENERICA),
    Rows(["bienes y servicios"]),
    ClickBtn(BTN.DEPARTAMENTO),
]

df = MEFScraper(steps).run(2022).result
```

---

## Example 3 — Using `Search` for Large Tables

When the municipality table exceeds 400 rows, the MEF shows a search box. Use `Search` to filter it server-side before selecting rows:

```python
steps = [
    Rows(["total"]),
    ClickBtn(BTN.CATEGORIA_PRESUPUESTAL),
    Search("poblacion"),           # filter budget category table by "poblacion"
    Rows(["edu"]),                 # then pick rows matching "edu"
    ClickBtn(BTN.NIVEL_GOBIERNO),
    Rows(["locales"]),
    ClickBtn(BTN.GOB_LOCALES_MANCOMUNIDADES),
    Rows(),                        # all sub-types
    ClickBtn(BTN.DEPARTAMENTO),
]

df = MEFScraper(steps).run(2020).result
print(df)
```

---

## Example 4 — Revenue (Ingreso) Data

Switch to ingreso mode to query revenue instead of expenditure:

```python
steps = [
    Rows(["total"]),
    ClickBtn(BTN.NIVEL_GOBIERNO),
    Rows(["locales"]),
    ClickBtn(BTN.RUBRO),
    Rows(),
    ClickBtn(BTN.DEPARTAMENTO),
]

df = MEFScraper(steps, tipo="ingreso").run(2021).result
print(df.columns.tolist())
# ['codigo_grp', 'concepto_region', 'pia', 'pim', 'recaudado', ...]
```

---

## Example 5 — Historical Multi-Year Query

Loop over years and concatenate results:

```python
import pandas as pd

steps = [
    Rows(["total"]),
    ClickBtn(BTN.NIVEL_GOBIERNO),
    Rows(["locales"]),
    ClickBtn(BTN.DEPARTAMENTO),
]

scraper = MEFScraper(steps)
frames = [scraper.run(y).result for y in range(2018, 2024)]
df_all = pd.concat(frames, ignore_index=True)
print(df_all.groupby("year")["devengado"].sum())
```

---

## Example 6 — Inspecting Steps Before Running

Validate your workflow without making any HTTP requests:

```python
from perustats.MEF import MEFScraper
from perustats.MEF.constants import buttons as BTN
from perustats.MEF.steps.click import ClickBtn, Rows
from rich import print

steps = [
    Rows(["total"]),
    ClickBtn(BTN.NIVEL_GOBIERNO),
    Rows(["locales"]),
    ClickBtn(BTN.DEPARTAMENTO),
]

scraper = MEFScraper(steps)
print(scraper.steps)
# [
#   Step(rows=Rows(['total']), click=ClickBtn(name=TipoGobierno)),
#   Step(rows=Rows(['locales']), click=ClickBtn(name=Departamento)),
# ]
```

---

## Example 7 — Projects Only (`act_proy`)

Query only *Proyectos* (capital investment) rather than the default mix:

```python
steps = [
    Rows(["total"]),
    ClickBtn(BTN.NIVEL_GOBIERNO),
    Rows(["locales"]),
    ClickBtn(BTN.GENERICA),
    Rows(),
    ClickBtn(BTN.DEPARTAMENTO),
]

df = MEFScraper(steps, act_proy="Proyecto").run(2023).result
```
