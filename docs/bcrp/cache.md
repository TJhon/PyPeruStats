# BCRPCache

`BCRPCache` provides a thin SQLite-backed persistence layer for BCRP time series data. It is used internally by `BCRPDataSeries` and can also be used directly for cache introspection or maintenance.

---

## Class signature

```python
class BCRPCache:
    def __init__(self, db_path: str) -> None
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `db_path` | `str` | Path to the SQLite file. Parent directories are created automatically if they do not exist. |

---

## Caching strategy

Each unique combination of `(frequency, start_date, end_date)` gets its own SQLite table:

```
series_{FREQ}_{start}_{end}
```

For example, a monthly query from `2020-01` to `2024-12` produces:

```
series_M_2020_01_2024_12
```

**Adding new codes to an existing range** does not recreate the table — new codes are fetched individually and merged in via `ALTER TABLE`-style outer join. This makes incremental queries fast.

---

## Methods

### `cached_codes`

```python
def cached_codes(self, freq: str, start_date: str, end_date: str) -> set[str]
```

Return the set of codes already stored for the given frequency and date range. Returns an empty set if the table does not yet exist.

```python
from perustats.BCRP.cache import BCRPCache

cache = BCRPCache("./data/bcrp_cache.db")
cached = cache.cached_codes("M", "2020-01", "2024-12")
print(cached)  # {'RD13761DM', 'PD04657MD'}
```

---

### `load`

```python
def load(
    self,
    freq: str,
    start_date: str,
    end_date: str,
    codes: list[str],
) -> pd.DataFrame | None
```

Load a DataFrame for the requested codes from the cache. Returns `None` if the table does not exist or none of the requested codes are cached.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `freq` | `str` | Frequency indicator (`"D"`, `"M"`, `"Q"`, `"A"`) |
| `start_date` | `str` | API-formatted start date |
| `end_date` | `str` | API-formatted end date |
| `codes` | `list[str]` | Codes to retrieve |

---

### `save`

```python
def save(
    self,
    df: pd.DataFrame,
    freq: str,
    start_date: str,
    end_date: str,
) -> None
```

Persist a DataFrame to the appropriate cache table.

- If the table does not exist it is created.
- If the table already exists, new columns are added and rows are merged (outer join on `date`).
- No-ops silently if `df` is `None` or empty.

---

### `clean_cache`

```python
def clean_cache(self) -> None
```

Drop all series tables from the database. The `metadata` table (series catalogue) is preserved.

```python
from perustats.BCRP.cache import BCRPCache

BCRPCache("./data/bcrp_cache.db").clean_cache()
```

!!! warning
    This permanently deletes all cached series data. The next `fetch_data()` call will re-download everything from the BCRP API.

---

### `list_cached_series`

```python
def list_cached_series(self) -> list[dict]
```

Introspect all series tables currently in the cache. Useful for auditing what has been downloaded.

#### Returns

A list of dictionaries with keys:

| Key | Description |
|---|---|
| `table` | Raw SQLite table name |
| `freq` | Frequency indicator |
| `start` | Start date used for the table |
| `end` | End date used for the table |
| `codes` | List of series codes stored in the table |

#### Example

```python
cache = BCRPCache("./data/bcrp_cache.db")

for entry in cache.list_cached_series():
    print(entry["freq"], entry["start"], "→", entry["end"], "|", entry["codes"])
# M 2020_01 → 2024_12 | ['RD13761DM', 'PD04657MD']
# A 2010 → 2023 | ['RD16085DA', 'CD10401DA']
```

---

### `load_valid_codes` / `save_valid_codes`

```python
def load_valid_codes(self) -> pd.DataFrame | None
def save_valid_codes(self, df: pd.DataFrame) -> None
```

Manage the `valid_codes_cache` accumulator table, which stores metadata for every code that has been successfully validated. The table uses `code` as a unique key so re-saving an already-seen code is a no-op.

---

## Database layout

```
bcrp_cache.db
├── metadata                          ← scraped BCRP catalogue (BCRPMetadata)
├── series_D_2020-01-01_2024-12-31   ← daily series table
├── series_M_2020-01_2024-12         ← monthly series table
├── series_Q_2020-1_2024-4           ← quarterly series table
└── series_A_2020_2024               ← annual series table
```
