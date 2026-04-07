# PeruStats

**Python tools to download and process public datasets from Peru.**

PeruStats provides a unified, developer-friendly interface to Peru's main public data portals — scraping, caching, and organizing microdata so you can focus on analysis instead of plumbing.

```bash
pip install perustats
```

---

## Data Sources

| Module           | Source                                                              | Status         |
| ---------------- | ------------------------------------------------------------------- | -------------- |
| `perustats.inei` | INEI — National microdata surveys (ENAHO, ENDES, ENAPRES, RENAMU …) | ✅ Available   |
| `perustats.bcrp` | BCRP — Central Bank time series                                     | ✅ Available   |
| `perustats.siaf` | MEF/SIAF — Public expenditure data                                  | 🚧 Coming soon |

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
from perustats import BCRPDataSeries, BCRPSeries

series = BCRPSeries(
    [
        " RD16085DA",
        "PD04657MD",
        "PD04646PD",
        "RD13761DM",
        "RD13805DM",
        "      RD13845DM",
        "RD15478DQ",
        "RD14266DQ",
        "CD10401DA",
        "CD10422DA",
        "fakecodeA",
    ],
    start_date="2000-01-02",
    end_date="2020-01-01",
)
data = BCRPDataSeries(series).fetch_data()

for freq in data.result.keys():
    print(data.result.get(freq))

```

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/TJhon/PyPeruStats).

## Contact

**Jhon K. Flores Rojas** — fr.jhonk@gmail.com
