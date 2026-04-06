# BCRP Time Series

!!! warning "Documentation in progress"
    This page is a placeholder. Full documentation for `perustats.bcrp` will be added when the source code is finalized.

The `perustats.bcrp` module retrieves time-series data from the **Banco Central de Reserva del Perú (BCRP)** statistical portal.

---

## Planned Features

- Retrieval of daily, monthly, quarterly, and annual series by code.
- Automatic parsing of BCRP's non-standard Spanish date formats (`"Ene05"`, `"T113"`, `"31Ene05"` …).
- Parallel processing of multiple series codes.
- Built-in SQLite caching.
- Output as tidy `pandas` DataFrames keyed by frequency (`"D"`, `"M"`, `"Q"`, `"A"`).

---

## Quick Preview

```python
from perustats import BCRPDataProcessor

processor = BCRPDataProcessor(
    series=["PD38032DD", "RD38085BM", "PD37940PQ"],
    start_date="2005-01-01",
    end_date="2023-12-31",
    parallel=True,
)

data = processor.process_data(save_sqlite=True)

daily_df     = data.get("D")
monthly_df   = data.get("M")
quarterly_df = data.get("Q")
annual_df    = data.get("A")
```

---

Check back soon for the full API reference.
