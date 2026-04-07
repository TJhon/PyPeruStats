# BCRPDataSeries

`BCRPDataSeries` is the main entry point for downloading BCRP data. It orchestrates metadata validation, HTTP fetching, date parsing, and SQLite caching.

---

## Class signature

```python
class BCRPDataSeries:
    def __init__(self, series: BCRPSeries, format_date: str = "%Y-%m-%d") -> None
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `series` | `BCRPSeries` | — | Query object with codes and date range |
| `format_date` | `str` | `"%Y-%m-%d"` | `strptime` format used when parsing dates internally |

---

## Methods

### `fetch_data`

```python
def fetch_data(
    self,
    cache: str | None = None,
    quater_to_timestamp: bool = True,
    use_code_names: bool = True,
) -> BCRPDataSeries
```

Fetch, cache, and parse all requested series. Returns `self` so calls can be chained.

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `cache` | `str \| None` | `None` | Path to the SQLite cache file. Defaults to `./data/bcrp_cache.db` |
| `quater_to_timestamp` | `bool` | `True` | Convert quarterly periods to end-of-quarter `Timestamp`. Set `False` to keep `pd.Period` objects |
| `use_code_names` | `bool` | `True` | Rename DataFrame columns from raw API codes to human-readable catalogue descriptions |

#### Returns

`BCRPDataSeries` — the same instance, with `.result` and `.valid_codes` populated.

#### Raises

| Exception | When |
|---|---|
| `requests.RequestException` | Network error during the API call |
| `ValueError` | `BCRPSeries.codes` is empty |

#### Notes

- On the first run for a given set of parameters the method makes an HTTP request and writes the result to the cache.
- On subsequent runs with identical `(freq, start_date, end_date)` parameters, data is loaded entirely from SQLite — no network call is made.
- New codes added to an existing date range are fetched incrementally and merged into the cached table.

---

### `df_date_format`

```python
def df_date_format(self, df: pd.DataFrame) -> pd.DataFrame
```

Parse the `date` column of *df* to `datetime64`. Called internally by `fetch_data`; exposed publicly for custom post-processing pipelines.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `df` | `pd.DataFrame` | DataFrame with a string `date` column |

#### Returns

`pd.DataFrame` — same frame with `date` as `datetime64[ns]`.

---

## Instance attributes (after `fetch_data`)

| Attribute | Type | Description |
|---|---|---|
| `result` | `dict[str, pd.DataFrame]` | Frequency → DataFrame mapping. Keys are canonical indicators: `"D"`, `"M"`, `"Q"`, `"A"` |
| `valid_codes` | `list[str]` | Codes that passed metadata validation |
| `series` | `BCRPSeries` | The original query object |

---

## Full example

```python
from perustats.BCRP.models import BCRPSeries
from perustats.BCRP.fetcher import BCRPDataSeries

series = BCRPSeries(
    codes=[
        "RD16085DA",   # annual
        "RD13761DM",   # monthly
        "RD15478DQ",   # quarterly
    ],
    start_date="2005-01-01",
    end_date="2023-12-31",
)

ds = BCRPDataSeries(series).fetch_data(
    cache="./cache/bcrp.db",
    quater_to_timestamp=True,
)

print(ds.valid_codes)
# ['RD16085DA', 'RD13761DM', 'RD15478DQ']

annual_df = ds.result["A"]
print(annual_df.dtypes)
# date         datetime64[ns]
# rd16085da    float64

monthly_df = ds.result["M"]
print(monthly_df.head())
```

---

## Incremental fetch example

The cache layer means you can extend an existing request without re-downloading already-cached series:

```python
# First request — downloads and caches 3 series
s1 = BCRPSeries(["RD16085DA", "RD14266DQ"], "2010-01-01", "2023-12-31")
BCRPDataSeries(s1).fetch_data()

# Second request — only the two new codes hit the API
s2 = BCRPSeries(
    ["RD16085DA", "RD14266DQ", "RD15238DQ", "RD15239DQ"],
    "2010-01-01",
    "2023-12-31",
)
result = BCRPDataSeries(s2).fetch_data()
```
