# Configuration Reference

`MEFScraper` automatically selects the correct MEF portal URL and column schema based on the requested year. This page documents the internals for contributors and advanced users.

---

## `Config` Dataclass

```python
from perustats.MEF.constants.config import Config

@dataclass(frozen=True)
class Config:
    years: range        # supported year range for this version
    url: str            # URL template with {year} and optionally {ap} placeholders
    columns: List[str]  # ordered list of column names for this version
```

`Config` instances are immutable (`frozen=True`). You should not need to create them manually — use `get_config()` instead.

---

## `get_config`

```python
from perustats.MEF.constants.config import get_config

get_config(year: int, tipo: Literal["gasto", "ingreso"] = "gasto") -> Config
```

Returns the `Config` object for the given year and query type.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `year` | `int` | — | Fiscal year to query. |
| `tipo` | `"gasto"` \| `"ingreso"` | `"gasto"` | Query type. |

### Raises

`ValueError` — if `year` is outside all known ranges for the given `tipo`.

### Example

```python
cfg = get_config(2020, "gasto")
print(cfg.url)      # https://apps5.mineco.gob.pe/.../Navegar_6.aspx?y={year}&ap={ap}
print(cfg.columns)  # ['codigo_grp', 'concepto_region', 'pia', ...]
```

---

## Version Mapping

### Gasto (Expenditure)

| Key | Years | URL Template | Column Schema |
|-----|-------|-------------|---------------|
| `v4` | 2009–2011 | `Navegar_4.aspx?y={year}&ap={ap}` | `COLUMNS_GASTO_V4` |
| `v5` | 2012–2015 | `Navegar_5.aspx?y={year}&ap={ap}` | `COLUMNS_GASTO_V5` |
| `v6` | 2016–2023 | `Navegar_6.aspx?y={year}&ap={ap}` | `COLUMNS_GASTO_V5` |
| `v7` | 2024–2026 | `Navegador/Navegar_7.aspx?y={year}&ap={ap}` | `COLUMNS_GASTO_V5` |

### Ingreso (Revenue)

| Key | Years | URL Template | Column Schema |
|-----|-------|-------------|---------------|
| `v4` | 2009–2011 | `Navegar_4.aspx?y={year}` | `COLUMNS_INGRESO` |
| `v5` | 2012–2015 | `Navegar_5.aspx?y={year}` | `COLUMNS_INGRESO` |
| `v6` | 2016–2026 | `Navegar_6.aspx?y={year}` | `COLUMNS_INGRESO` |

---

## Column Schemas

### `COLUMNS_GASTO_V4` (2009–2011)

```python
["codigo_grp", "concepto_region", "pia", "pim",
 "compromiso", "devengado", "girado", "avance_p"]
```

### `COLUMNS_GASTO_V5` (2012–present)

```python
["codigo_grp", "concepto_region", "pia", "pim",
 "certificacion", "compromiso_anual",
 "atencion_de_compromiso_mensual",
 "devengado", "girado", "avance_p"]
```

### `COLUMNS_INGRESO` (all years)

```python
["codigo_grp", "concepto_region", "pia", "pim", "recaudado"]
```

---

## URL Templates

Base URLs are defined in `perustats.MEF.constants.reference`:

```python
# Gasto
GASTO_URL_V4 = "https://apps5.mineco.gob.pe/transparencia/mensual/Navegar_4.aspx?y={year}&ap={ap}"
GASTO_URL_V5 = "https://apps5.mineco.gob.pe/transparencia/mensual/Navegar_5.aspx?y={year}&ap={ap}"
GASTO_URL_V6 = "https://apps5.mineco.gob.pe/transparencia/mensual/Navegar_6.aspx?y={year}&ap={ap}"
GASTO_URL_V7 = "https://apps5.mineco.gob.pe/transparencia/Navegador/Navegar_7.aspx?y={year}&ap={ap}"

# Ingreso
INGRESO_URL_V4 = "https://apps5.mineco.gob.pe/transparenciaingresos/Navegador/Navegar_4.aspx?y={year}"
INGRESO_URL_V5 = "https://apps5.mineco.gob.pe/transparenciaingresos/Navegador/Navegar_5.aspx?y={year}"
INGRESO_URL_V6 = "https://apps5.mineco.gob.pe/transparenciaingresos/Navegador/Navegar_6.aspx?y={year}"
```

The `{year}` and `{ap}` placeholders are filled in by `MEFScraper._setup_year()` before the HTTP session is initialized.
