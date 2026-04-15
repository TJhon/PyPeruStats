# MEF — Consulta Amigable del Presupuesto Público

The **MEF** module provides an unofficial Python API to automate data extraction from Peru's Ministry of Economy and Finance (Ministerio de Economía y Finanzas) **Consulta Amigable** portal. It covers both **spending (gasto)** and **revenue (ingreso)** data from 2009 onwards.

---

## What is Consulta Amigable?

[Consulta Amigable](https://apps5.mineco.gob.pe/transparencia/Navegador/Navegar_7.aspx) is the MEF's public transparency portal where citizens and researchers can explore Peru's national budget execution. It exposes a hierarchical browser interface that lets you drill down through levels of government, geographic regions, budget categories, and more.

`perustats.MEF` replaces manual point-and-click navigation with a **declarative step-based API** that mirrors the human interaction flow.

---

## Key Features

- ✅ **Declarative workflow** — describe navigation steps in plain Python; the scraper handles HTTP, HTML parsing, and pagination.
- ✅ **Gasto & Ingreso** — query both expenditure and revenue datasets.
- ✅ **Multi-year support** — data from 2009 to the present, with automatic platform-version detection (v4 → v7).
- ✅ **Fuzzy row filtering** — use keyword fragments to match rows without needing exact text.
- ✅ **Search panel support** — handles large tables (400+ rows) through the MEF's built-in search API.
- ✅ **Pandas output** — results are returned as `pd.DataFrame` objects ready for analysis.
- 🔜 **Partial saves** — checkpoint progress to disk mid-scrape _(coming soon)_.
- 🔜 **Progress bars** — rich visual feedback for long-running workflows _(coming soon)_.

---

## Installation

```bash
pip install perustats
```

---

## Quick Example

```python
from perustats import MEFScraper
from perustats.MEF.constants import buttons as BTN
from perustats.MEF.steps.click import ClickBtn, Rows

steps = [
    Rows(["total"]),
    ClickBtn(BTN.NIVEL_GOBIERNO),
    Rows(["locales"]),
    ClickBtn(BTN.GENERICA),
    Rows(["bienes y servicios"]),
    ClickBtn(BTN.DEPARTAMENTO),
]

df = MEFScraper(steps).run(2023).result
print(df.head())
```

---

## Module Structure

```
perustats/MEF/
├── __init__.py          # Public API surface
├── scrapper.py          # MEFScraper — orchestrates the full workflow
├── constants/
│   ├── buttons.py       # Button ID constants (BTN.*)
│   ├── config.py        # URL + column configs per platform version
│   ├── reference.py     # Raw URL templates and HTTP headers
│   └── tables.py        # Column name lists per version
├── steps/
│   ├── click.py         # Rows, ClickBtn, Search, SavePartial primitives
│   └── workflow.py      # Workflow parser — converts flat lists to Step objects
└── utils/               # Internal HTTP, HTML, and parsing helpers (not public API)
```

---

## Navigation

| Page                               | Description                                 |
| ---------------------------------- | ------------------------------------------- |
| [Quickstart](quickstart.md)        | Step-by-step guide to your first query      |
| [MEFScraper Reference](scraper.md) | Full API reference for the main class       |
| [Step Primitives](steps.md)        | `Rows`, `ClickBtn`, `Search`, `SavePartial` |
| [Button Constants](buttons.md)     | All available `BTN.*` constants             |
| [Configuration](config.md)         | Version detection and `Config` dataclass    |
| [Examples](examples.md)            | Real-world scraping recipes                 |
| [TODO](todo.md)                    | Planned features and roadmap                |
