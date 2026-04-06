# Installation & Quickstart

## Installation

PeruStats is published on PyPI and can be installed with `pip`:

```bash
pip install perustats
```

Python **3.9 or later** is required.

---

## Minimal Example

```python
from perustats.inei import INEIFetcher

fetcher = INEIFetcher(
    survey="enaho",
    years=range(2020, 2024),
)

fetcher.fetch_modules().download(module_codes=[1, 2, 5]).organize(organize_by="year")
```

That's it. After this runs you will find the organized files under `./data/microdatos_inei/enaho/2_organized/by_year/`.

---

## Step-by-Step Breakdown

### 1 — Create the fetcher

```python
from perustats.inei import INEIFetcher

fetcher = INEIFetcher(
    survey="enaho",           # survey code
    years=range(2018, 2024),  # years to cover
    master_directory="./data",
    parallel_jobs=4,
)
```

### 2 — Fetch the module listing

```python
fetcher.fetch_modules()
```

This call scrapes the INEI portal for each requested year and stores the result in a local SQLite database (`referrer.db`). Subsequent runs load from the cache instead of hitting the network.

After the call completes, the module catalogue is available as a DataFrame:

```python
print(fetcher.modules_df[["year_ref", "module_code", "stata", "csv"]].head())
```

### 3 — Download ZIP files

```python
fetcher.download(
    module_codes=[1, 2, 5],   # None = download everything
    force=False,               # skip existing valid ZIPs
    remove_zip_after_extract=False,
)
```

ZIPs are saved to `0_zips/` and extracted to `1_unzipped/`.

### 4 — Organize extracted files

```python
fetcher.organize(
    organize_by="year",        # or "module"
    operation="copy",          # or "move" to save disk space
    deduplicate_docs_by_hash=True,
)
```

Files are placed in `2_organized/by_year/` (or `by_module/`). Documentation PDFs are deduplicated by content hash when `deduplicate_docs_by_hash=True`.

---

## Method Chaining

All three methods return `self`, so you can chain them:

```python
(INEIFetcher("endes", years=range(2015, 2024))
    .fetch_modules()
    .download(module_codes=[64, 65, 73])
    .organize(organize_by="module", operation="move"))
```

---

## Checking Available Surveys

```python
from perustats.inei import registry

print(registry.list_codes())
# ['enaho', 'enaho_panel', 'enapres', 'endes', 'renamu']
```
