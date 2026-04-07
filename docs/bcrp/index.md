# BCRP — Central Reserve Bank of Peru

The `BCRP` module lets you download, cache, and work with **any time-series published by the Peruvian Central Reserve Bank** through its public statistics API.

---

## What it does

| Capability | Details |
|---|---|
| **Fetch data** | Pulls one or many series in a single HTTP call |
| **Multi-frequency** | Daily (`D`), Monthly (`M`), Quarterly (`Q`), Annual (`A`) |
| **Metadata validation** | Warns about unknown codes *before* making any API request |
| **SQLite caching** | Re-running with the same parameters hits the local cache, not the network |
| **Pandas-ready** | Returns tidy `DataFrame` objects with a `datetime` index |

---

## Architecture overview

```
BCRPSeries          ← define your query (codes + date range)
    │
    ▼
BCRPDataSeries      ← orchestrates fetch, cache, and date parsing
    ├── BCRPMetadata   validates codes against the scraped catalogue
    └── BCRPCache      reads / writes the SQLite cache
```

---

## Quick example

```python
from perustats.BCRP.models import BCRPSeries
from perustats.BCRP.fetcher import BCRPDataSeries

series = BCRPSeries(
    codes=["RD16085DA", "PD04657MD", "RD14266DQ"],
    start_date="2015-01-01",
    end_date="2024-12-31",
)

result = BCRPDataSeries(series).fetch_data()

# result.result is a dict keyed by frequency
daily_df     = result.result["D"]
monthly_df   = result.result["M"]
quarterly_df = result.result["Q"]

print(daily_df.head())
```

---

## Series code format

Every BCRP series code encodes its own frequency in the **last character**:

| Suffix | Frequency |
|---|---|
| `D` | Daily |
| `M` | Monthly |
| `Q` | Quarterly |
| `A` | Annual |

Example: `RD16085D**A**` → annual series. The library reads this suffix automatically and routes each code to the correct API endpoint and date format.

---

## Pages in this section

| Page | Description |
|---|---|
| [Quickstart](quickstart.md) | Installation and a working end-to-end example |
| [BCRPDataSeries](fetcher.md) | Full API reference for the main fetcher class |
| [BCRPSeries model](series.md) | Query model — codes, date range, and frequency grouping |
| [BCRPMetadata](metadata.md) | Catalogue management and code search |
| [BCRPCache](cache.md) | SQLite cache internals |
| [Examples](examples.md) | Real-world usage patterns |
