# INEI Microdata

The `perustats.inei` module provides a high-level interface to download, extract, and organize microdata published by Peru's **Instituto Nacional de Estadística e Informática (INEI)** at [proyectos.inei.gob.pe/microdatos](https://proyectos.inei.gob.pe/microdatos).

---

## Available Surveys

| Code | Survey | Periodicity |
|------|--------|-------------|
| `enaho` | Encuesta Nacional de Hogares — Condiciones de Vida y Pobreza | Annual |
| `enaho_panel` | ENAHO Panel | Panel |
| `endes` | Encuesta Demográfica y de Salud Familiar | Annual |
| `enapres` | Encuesta Nacional de Programas Presupuestales | Annual |
| `renamu` | Registro Nacional de Municipalidades | Annual |

!!! tip "Adding new surveys"
    New surveys can be registered at runtime with a single line — no source edits needed.
    See the [Survey Registry](surveys.md) page for details.

---

## Key Features

- **Three-step fluent API**: `fetch_modules()` → `download()` → `organize()` — all chainable.
- **Parallel downloads** with configurable worker threads.
- **SQLite caching** — module lists are cached locally so repeated runs skip the network.
- **Multiple formats**: Stata (`.dta`), SPSS (`.sav`), CSV, dBASE (`.dbf`).
- **Automatic ZIP validation**: corrupted archives are detected and re-downloaded.
- **Smart deduplication** of documentation files via content hashing.
- **Flexible organization**: sort extracted files by year or by module.

---

## Three-Step Workflow

```
INEIFetcher(survey, years)
      │
      ▼
 fetch_modules()          ← scrapes/caches module listing per year
      │
      ▼
   download()             ← downloads & extracts ZIP files in parallel
      │
      ▼
   organize()             ← sorts files into by_year/ or by_module/
```

Proceed to [Installation & Quickstart](quickstart.md) to get started.
