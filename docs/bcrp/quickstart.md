# Installation & Quickstart

## Installation

```bash
pip install perustats
```

The BCRP module requires:

- `pandas`
- `requests`
- `beautifulsoup4`
- `tqdm`
- `rich`

All dependencies are installed automatically with `perustats`.

---

## Your first request

### 1. Define the series you want

```python
from perustats.BCRP.models import BCRPSeries

series = BCRPSeries(
    codes=["RD16085DA", "PD04657MD"],  # (1)
    start_date="2020-01-01",
    end_date="2024-12-31",
)
```

1. The last character of each code identifies the frequency: `D` = daily, `M` = monthly, `Q` = quarterly, `A` = annual.

### 2. Fetch the data

```python
from perustats.BCRP.fetcher import BCRPDataSeries

result = BCRPDataSeries(series).fetch_data()
```

On **first run** the library scrapes the BCRP website to build a local metadata catalogue (`~10 s`). Every subsequent run loads from SQLite instantly.

### 3. Access the DataFrames

`fetch_data()` returns the same `BCRPDataSeries` instance. The data lives in `result.result`, a dictionary keyed by canonical frequency:

```python
# Keys present depend on the frequencies in your codes list
annual_df   = result.result.get("A")
monthly_df  = result.result.get("M")
```

Each value is a `pandas.DataFrame` with:

- a `date` column (parsed `datetime64`)
- one column per series code (named after its catalogue description)

```python
print(annual_df)
#          date  rd16085da
# 0  2020-12-31    45230.5
# 1  2021-12-31    49870.3
# ...
```

---

## Mixed-frequency request

You can request series with different frequencies in a single call — the library groups them automatically:

```python
series = BCRPSeries(
    codes=[
        "RD16085DA",   # annual
        "PD04657MD",   # monthly
        "RD14266DQ",   # quarterly
        "PD04646PD",   # daily
    ],
    start_date="2010-01-01",
    end_date="2024-12-31",
)

result = BCRPDataSeries(series).fetch_data()

for freq, df in result.result.items():
    print(f"{freq}: {df.shape}")
# A: (14, 2)
# M: (180, 2)
# Q: (56, 2)
# D: (3652, 2)
```

---

## Invalid codes

Unknown codes are skipped with a `UserWarning` — the rest of the request still succeeds:

```python
series = BCRPSeries(
    codes=["RD16085DA", "FAKE_CODE"],
    start_date="2020-01-01",
    end_date="2024-12-31",
)
result = BCRPDataSeries(series).fetch_data()
# UserWarning: The following codes were not found in the BCRP catalogue
# and will be skipped: ['FAKE_CODE']
```

---

## Caching behaviour

By default the cache database is written to `./data/bcrp_cache.db`. Pass a custom path to `fetch_data()`:

```python
result = BCRPDataSeries(series).fetch_data(cache="~/my_project/bcrp.db")
```

To clear all cached series data (metadata is preserved):

```python
from perustats.BCRP.cache import BCRPCache

BCRPCache("./data/bcrp_cache.db").clean_cache()
```

---

## Next steps

- Browse [Examples](examples.md) for real-world patterns
- See [BCRPDataSeries reference](fetcher.md) for all `fetch_data()` options
- Use [BCRPMetadata](metadata.md) to search for series codes by keyword
