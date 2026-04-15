# Installation & Quickstart

This guide walks you through installing `perustats` and running your first MEF query in under five minutes.

---

## Installation

```bash
pip install perustats
```

Dependencies pulled in automatically: `requests`, `beautifulsoup4`, `pandas`, `rich`.

---

## Core Concept: Steps

The MEF portal works like a drill-down browser — you click a button to load a new table, then select a row, then click another button, and so on. `perustats.MEF` models this as a **flat list of alternating `Rows` → `ClickBtn` pairs** that the `Workflow` parser converts into structured `Step` objects internally.

```
[Rows(filter), ClickBtn(button), Rows(filter), ClickBtn(button), ...]
```

Each pair means: *"filter the current table to rows matching these keywords, then click this button."*

---

## Your First Query

### 1. Import the pieces

```python
from perustats.MEF import MEFScraper
from perustats.MEF.constants import buttons as BTN
from perustats.MEF.steps.click import ClickBtn, Rows
```

### 2. Define your navigation steps

```python
steps = [
    Rows(["total"]),              # start at "Total" row
    ClickBtn(BTN.NIVEL_GOBIERNO), # click "Nivel de Gobierno"
    Rows(["locales"]),            # select "Gobiernos Locales"
    ClickBtn(BTN.GENERICA),       # click "Genérica de Gasto"
    Rows(["bienes y servicios"]), # filter to "Bienes y Servicios"
    ClickBtn(BTN.DEPARTAMENTO),   # final drill-down: by department
]
```

### 3. Run the scraper

```python
scraper = MEFScraper(steps)
result = scraper.run(2023)

print(result.result)
```

`result.result` is a `pd.DataFrame` with budget execution columns for each department.

---

## Choosing Gasto vs Ingreso

By default `MEFScraper` queries **expenditure (gasto)**. To query **revenue (ingreso)**:

```python
scraper = MEFScraper(steps, tipo="ingreso")
```

---

## Filtering Rows

`Rows` accepts a list of **case-insensitive regex fragments**. Any row whose text contains at least one fragment is kept. Pass an **empty list** (or just `Rows()`) to iterate over *all* rows:

```python
Rows(["ica", "junin", "piura"])  # only these three departments
Rows()                            # every row in the table
```

---

## The `as_column` Flag

By default, `ClickBtn` records the value of each row it visits as an extra metadata column in the final DataFrame. Set `as_column=False` when you want to navigate through a level without recording it:

```python
ClickBtn(BTN.GOB_LOCALES_MANCOMUNIDADES, as_column=False)
```

---

## Handling Large Tables with `Search`

When a table exceeds ~400 rows, the MEF portal hides entries and shows a search box. Use `Search` immediately after a `ClickBtn` to send a query to the MEF's backend before the next `Rows` filter runs:

```python
steps = [
    ...
    Rows(["locales"]),
    ClickBtn(BTN.MUNICIPALIDAD),
    Search("provincial"),          # searches for "provincial" in description
    Rows(["lima"]),
    ClickBtn(BTN.GENERICA),
]
```

---

## Selecting `act_proy`

For expenditure queries, you can switch between *Actividades/Proyectos*, *Actividades only*, or *Proyectos only*:

```python
MEFScraper(steps, act_proy="Actividad")   # default: "ActProy"
MEFScraper(steps, act_proy="Proyecto")
```

---

## Full Working Example

```python
from perustats.MEF import MEFScraper
from perustats.MEF.constants import buttons as BTN
from perustats.MEF.steps.click import ClickBtn, Rows

# Spending on goods & services by local governments, broken down by department
steps = [
    Rows(["total"]),
    ClickBtn(BTN.NIVEL_GOBIERNO),
    Rows(["locales"]),
    ClickBtn(BTN.GOB_LOCALES_MANCOMUNIDADES, as_column=False),
    Rows(["municipal"]),
    ClickBtn(BTN.GENERICA),
    Rows(["bienes y servicios", "deuda publica"]),
    ClickBtn(BTN.DEPARTAMENTO),
    Rows(["ancash", "lima"]),
    ClickBtn(BTN.MUNICIPALIDAD),
]

df = MEFScraper(steps, convert_numeric=True).run(2022).result
print(df)
```

---

## Next Steps

- [MEFScraper Reference](scraper.md) — full parameter and method documentation
- [Step Primitives](steps.md) — all building blocks explained
- [Button Constants](buttons.md) — every available button ID
- [Examples](examples.md) — more real-world recipes
