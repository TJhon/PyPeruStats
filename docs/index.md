# PeruStats

**Python tools to download and process public datasets from Peru.**

PeruStats provides a unified, developer-friendly interface to Peru's main public data portals — scraping, caching, and organizing microdata so you can focus on analysis instead of plumbing.

```bash
pip install perustats
```

---

## Data Sources

| Module | Source | Status |
|--------|--------|--------|
| `perustats.inei` | INEI — National microdata surveys (ENAHO, ENDES, ENAPRES, RENAMU …) | ✅ Available |
| `perustats.bcrp` | BCRP — Central Bank time series | ✅ Available |
| `perustats.siaf` | MEF/SIAF — Public expenditure data | 🚧 Coming soon |

---

## Quickstart

### INEI Microdata

Download and organize ENAHO survey data in three chained calls:

```python
from perustats.inei import INEIFetcher

fetcher = INEIFetcher(
    survey="enaho",
    years=range(2020, 2024),
    master_directory="./data",
)

(fetcher
    .fetch_modules()
    .download(module_codes=[1, 2, 5])
    .organize(organize_by="year"))
```

### BCRP Time Series

```python
from perustats import BCRPDataProcessor

processor = BCRPDataProcessor(
    ["PD38032DD", "RD38085BM"],
    start_date="2010-01-01",
    end_date="2023-12-31",
    parallel=True,
)
data = processor.process_data()
```

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/TJhon/PyPeruStats).

## Contact

**Jhon K. Flores Rojas** — fr.jhonk@gmail.com
