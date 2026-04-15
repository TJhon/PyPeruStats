# MEFScraper Reference

`MEFScraper` is the main class of the MEF module. It accepts a declarative list of navigation steps and executes them against the MEF Consulta Amigable portal, returning the collected data as a Pandas DataFrame.

---

## Class: `MEFScraper`

```python
from perustats.MEF import MEFScraper
```

### Constructor

```python
MEFScraper(
    steps: list = [],
    tipo: Literal["gasto", "ingreso"] = "gasto",
    act_proy: Literal["ActProy", "Actividad", "Proyecto"] = "ActProy",
    master_dir_save: str = "./data/mef/",
    convert_numeric: bool = True,
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `steps` | `list` | `[]` | Flat list of `Rows`, `ClickBtn`, `Search`, and `SavePartial` objects that describe the navigation workflow. See [Step Primitives](steps.md). |
| `tipo` | `"gasto"` \| `"ingreso"` | `"gasto"` | Whether to query expenditure or revenue data. |
| `act_proy` | `"ActProy"` \| `"Actividad"` \| `"Proyecto"` | `"ActProy"` | Filters the expenditure query to all activities+projects (`ActProy`), activities only, or projects only. Only applies when `tipo="gasto"`. |
| `master_dir_save` | `str` | `"./data/mef/"` | Root directory for saving partial results. Year and tipo sub-directories are created automatically. |
| `convert_numeric` | `bool` | `True` | When `True`, attempts to coerce budget columns to numeric types. Set to `False` to keep raw strings. |

#### Raises

- `ValueError` — if `tipo` is not `"gasto"` or `"ingreso"`.
- `ValueError` — if `act_proy` is invalid for the chosen `tipo`.

---

### Method: `run`

```python
scraper.run(year: int) -> MEFScraper
```

Executes the full navigation workflow for the given fiscal year and stores the result.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | `int` | Fiscal year to query. Supported range: **2009–2026** for gasto; **2009–2026** for ingreso. |

#### Returns

`self` — the `MEFScraper` instance, so calls can be chained:

```python
df = MEFScraper(steps).run(2023).result
```

#### Side Effects

- Sets `scraper.result` (`pd.DataFrame`) with the collected data.
- Sets `scraper.year`, `scraper.config`, `scraper.initial_session`, and `scraper.save_dir`.

---

### Attribute: `result`

```python
scraper.result  # pd.DataFrame
```

Available after calling `.run()`. Contains one row per leaf-level entity (e.g. municipality) with:

- All budget execution columns for the platform version (PIA, PIM, Devengado, etc.).
- Additional metadata columns added by each `ClickBtn(as_column=True)` step (e.g. `TipoGobierno`, `Generica`, `Departamento`).
- A `year` column.

#### Column reference by version

| Version | Years | Columns |
|---------|-------|---------|
| v4 | 2009–2011 | `codigo_grp`, `concepto_region`, `pia`, `pim`, `compromiso`, `devengado`, `girado`, `avance_p` |
| v5 / v6 / v7 | 2012–present | `codigo_grp`, `concepto_region`, `pia`, `pim`, `certificacion`, `compromiso_anual`, `atencion_de_compromiso_mensual`, `devengado`, `girado`, `avance_p` |
| Ingreso (all) | 2009–present | `codigo_grp`, `concepto_region`, `pia`, `pim`, `recaudado` |

---

### Attribute: `steps`

```python
scraper.steps  # list[Step]
```

The parsed, structured representation of the flat input list. Useful for debugging to verify the workflow was interpreted correctly before making HTTP requests.

```python
scraper = MEFScraper(steps)
print(scraper.steps)
# [Step(rows=Rows(['total']), click=ClickBtn(name=TipoGobierno)), ...]
```

---

## Platform Version Detection

`MEFScraper` automatically selects the correct MEF portal URL and column schema based on the requested year:

| Years | Gasto URL | Columns |
|-------|-----------|---------|
| 2009–2011 | `Navegar_4.aspx` | v4 |
| 2012–2015 | `Navegar_5.aspx` | v5 |
| 2016–2023 | `Navegar_6.aspx` | v5 |
| 2024–2026 | `Navegar_7.aspx` | v5 |

You do not need to configure this manually — just pass the year to `.run()`.

---

## Error Handling

```python
try:
    result = MEFScraper(steps).run(2023)
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Network or parsing error: {e}")
```

Common error causes:

- **Invalid year** — year outside the supported range raises `ValueError`.
- **Invalid `tipo` / `act_proy`** — raises `ValueError` at construction time.
- **Network errors** — the MEF portal occasionally returns 500 errors or times out; wrap `.run()` in a try/except and retry.
- **Missing `ClickBtn` in a step block** — the `Workflow` parser raises `ValueError` if a `Rows` block has no following `ClickBtn`.
