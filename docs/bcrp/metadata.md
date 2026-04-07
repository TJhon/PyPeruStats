# BCRPMetadata

`BCRPMetadata` manages the BCRP series catalogue. It scrapes the BCRP statistics website once, persists the result to SQLite, and exposes helpers to validate codes and search for series by keyword.

---

## Class signature

```python
class BCRPMetadata:
    def __init__(self, db_path: str = "./data/bcrp_cache.db") -> None
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `db_path` | `str` | `"./data/bcrp_cache.db"` | Path to the shared SQLite cache file |

On instantiation the class tries to load an existing catalogue from SQLite. If none is found, it scrapes the BCRP website automatically (~10 seconds) and saves the result.

---

## Methods

### `validate_codes`

```python
def validate_codes(
    self, codes: list[str]
) -> tuple[list[str], dict[str, str], pd.DataFrame, list[str]]
```

Check a list of codes against the downloaded catalogue.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `codes` | `list[str]` | Series codes to validate |

#### Returns

A 4-tuple:

| Position | Type | Description |
|---|---|---|
| 0 | `list[str]` | Valid codes found in the catalogue |
| 1 | `dict[str, str]` | Mapping of `"Group - Description"` → `code` (lowercase) for column renaming |
| 2 | `pd.DataFrame` | Metadata rows for valid codes |
| 3 | `list[str]` | Invalid codes not found in the catalogue |

A `UserWarning` is also emitted for invalid codes so they are visible even when the caller ignores the return value.

#### Example

```python
from perustats.BCRP.metadata import BCRPMetadata

meta = BCRPMetadata()

valid, names_map, df_valid, invalid = meta.validate_codes(
    ["RD16085DA", "MADE_UP_CODE"]
)

print(valid)    # ['RD16085DA']
print(invalid)  # ['MADE_UP_CODE']
# UserWarning: The following codes were not found in the BCRP catalogue
# and will be skipped: ['MADE_UP_CODE']
```

---

### `refresh`

```python
def refresh(self) -> None
```

Force a full re-scrape of the BCRP catalogue and overwrite the SQLite cache. Use this when you suspect new series have been published.

```python
meta = BCRPMetadata()
meta.refresh()
```

---

### `search`

```python
def search(self, query: str) -> pd.DataFrame
```

Return catalogue rows whose `description` field contains `query` (case-insensitive substring match).

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `query` | `str` | Free-text search term |

#### Returns

`pd.DataFrame` with columns `code`, `description`, `group`, `source`, `freq_label`, `freq`.

#### Example

```python
results = meta.search("tipo de cambio")
print(results[["code", "description", "freq"]].head())
#          code                          description freq
# 0  PD04640KD        Tipo de cambio compra - Dólares    D
# 1  PD04641KD        Tipo de cambio venta - Dólares     D
```

---

### `codes_for_frequency`

```python
def codes_for_frequency(self, frequency: str) -> list[str]
```

Return all known codes for a given frequency.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `frequency` | `str` | Canonical indicator (`"D"`, `"M"`, `"Q"`, `"A"`) or alias (`"daily"`, `"monthly"`, etc.) |

#### Returns

`list[str]` of all codes in that frequency bucket.

```python
monthly_codes = meta.codes_for_frequency("M")
print(f"{len(monthly_codes)} monthly series available")
```

---

## Properties

### `dataframe`

```python
@property
def dataframe(self) -> pd.DataFrame | None
```

The full catalogue as a DataFrame. Returns `None` if the catalogue has not been loaded yet.

```python
df = meta.dataframe
print(df.columns.tolist())
# ['code', 'description', 'fecha_inicio', 'fecha_fin', 'url',
#  'last_update', 'group', 'source', 'freq_label', 'freq']
```

---

## Catalogue schema

| Column | Description |
|---|---|
| `code` | BCRP series code (e.g. `RD16085DA`) |
| `description` | Human-readable series name |
| `group` | Thematic group on the BCRP website |
| `source` | Data source credited on the website |
| `freq_label` | Spanish frequency label from the website (`diarias`, `mensuales`, …) |
| `freq` | Canonical frequency indicator (`D`, `M`, `Q`, `A`) |
| `fecha_inicio` | Series start date as a string |
| `fecha_fin` | Series end date as a string |
| `last_update` | Date of the last published data point |
| `url` | Direct link to the series page on the BCRP website |
