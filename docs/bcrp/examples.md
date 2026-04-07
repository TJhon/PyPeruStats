# Examples

Practical recipes for common BCRP data tasks.

---

## 1. Exchange rate — daily series

```python
from perustats.BCRP.models import BCRPSeries
from perustats.BCRP.fetcher import BCRPDataSeries

series = BCRPSeries(
    codes=["PD04640KD", "PD04641KD"],  # USD buy / sell
    start_date="2020-01-01",
    end_date="2024-12-31",
)

result = BCRPDataSeries(series).fetch_data()
df = result.result["D"]

print(df.tail())
#          date  pd04640kd  pd04641kd
# ...  2024-12-30      3.721      3.725
```

---

## 2. GDP growth — annual series

```python
from perustats.BCRP.models import BCRPSeries, DEFAULT_START_DATE
from perustats.BCRP.fetcher import BCRPDataSeries
from datetime import date

series = BCRPSeries(
    codes=["RD16085DA"],
    start_date=DEFAULT_START_DATE,
    end_date=date.today().isoformat(),
)

result = BCRPDataSeries(series).fetch_data()
gdp = result.result["A"]

import matplotlib.pyplot as plt

gdp.plot(x="date", y=gdp.columns[1], title="Peru GDP (BCRP)")
plt.tight_layout()
plt.show()
```

---

## 3. Mixed-frequency in one call

```python
series = BCRPSeries(
    codes=[
        "CD10401DA",   # annual — fiscal balance
        "RD13761DM",   # monthly — CPI
        "RD15478DQ",   # quarterly — current account
    ],
    start_date="2010-01-01",
    end_date="2023-12-31",
)

result = BCRPDataSeries(series).fetch_data()

annual_df     = result.result["A"]
monthly_df    = result.result["M"]
quarterly_df  = result.result["Q"]
```

---

## 4. Search for series codes by keyword

```python
from perustats.BCRP.metadata import BCRPMetadata

meta = BCRPMetadata()

hits = meta.search("inflacion")
print(hits[["code", "description", "freq"]].to_string(index=False))
```

---

## 5. Discover all monthly codes

```python
from perustats.BCRP.metadata import BCRPMetadata

meta = BCRPMetadata()
monthly = meta.codes_for_frequency("monthly")
print(f"{len(monthly)} monthly series available")
print(monthly[:5])
```

---

## 6. Refresh the metadata catalogue

The catalogue is scraped once and cached. Call `refresh()` to pick up newly published series:

```python
from perustats.BCRP.metadata import BCRPMetadata

BCRPMetadata().refresh()
```

---

## 7. Inspect the local cache

```python
from perustats.BCRP.cache import BCRPCache

cache = BCRPCache("./data/bcrp_cache.db")

for entry in cache.list_cached_series():
    codes_str = ", ".join(entry["codes"])
    print(f"[{entry['freq']}] {entry['start']} → {entry['end']}: {codes_str}")
```

---

## 8. Clear cached series data

```python
from perustats.BCRP.cache import BCRPCache

# Wipes all series tables; metadata is preserved
BCRPCache("./data/bcrp_cache.db").clean_cache()
```

---

## 9. Custom cache location

```python
result = BCRPDataSeries(series).fetch_data(cache="/tmp/my_bcrp_cache.db")
```

---

## 10. Handling invalid codes gracefully

```python
import warnings
from perustats.BCRP.models import BCRPSeries
from perustats.BCRP.fetcher import BCRPDataSeries

codes_to_try = ["RD16085DA", "MAYBE_WRONG_CODE", "RD13761DM"]

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    result = BCRPDataSeries(
        BCRPSeries(codes_to_try, "2020-01-01", "2023-12-31")
    ).fetch_data()

skipped = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
if skipped:
    print("Skipped codes:", skipped)

print("Valid codes fetched:", result.valid_codes)
```
