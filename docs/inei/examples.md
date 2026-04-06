# Examples

A collection of practical recipes for common use-cases.

---

## Example 1 — ENAHO, single year, selective modules

```python
from perustats.inei import INEIFetcher

fetcher = INEIFetcher(
    survey="enaho",
    years=[2023],
    master_directory="./data",
)

fetcher.fetch_modules()

# Peek at what is available
print(fetcher.modules_df[["module_code", "stata", "csv"]].dropna(subset=["stata"]))

# Download modules 1, 2, and 5 (housing, household members, education)
fetcher.download(module_codes=[1, 2, 5])

# Organize by module for easy longitudinal stacking later
fetcher.organize(organize_by="module")
```

---

## Example 2 — ENDES, multiple years, multiple formats

```python
from perustats.inei import INEIFetcher

(INEIFetcher(
    survey="endes",
    years=range(2010, 2024),
    master_directory="./datos_inei",
    parallel_jobs=6,
)
.fetch_modules()
.download(
    module_codes=[64, 65, 73, 74],
    force=False,
    remove_zip_after_extract=False,
)
.organize(organize_by="year", operation="copy")
.organize(organize_by="module", operation="copy"))
```

!!! tip
    Calling `organize()` twice with different `organize_by` values is a valid pattern — the source files in `1_unzipped/` are not modified as long as `operation="copy"`.

---

## Example 3 — ENAPRES, save disk space

When storage is constrained, use `operation="move"` and remove ZIPs after extraction:

```python
from perustats.inei import INEIFetcher

(INEIFetcher("enapres", years=range(2015, 2024), parallel_jobs=4)
    .fetch_modules()
    .download(remove_zip_after_extract=True)
    .organize(organize_by="module", operation="move"))
```

---

## Example 4 — Inspect modules without downloading

```python
from perustats.inei import INEIFetcher

fetcher = INEIFetcher("enaho", years=[2021, 2022, 2023])
fetcher.fetch_modules()

df = fetcher.modules_df
print(df.shape)               # (rows, cols)
print(df["module_code"].unique())
print(df[df["stata"].notna()][["year_ref", "module_code", "stata"]])
```

---

## Example 5 — Registering a custom survey

```python
from perustats.inei import INEIFetcher, registry, Survey

# Register once at the top of your script/notebook
registry.register(Survey(
    code="enniv",
    name="Encuesta Nacional de Niveles de Vida",
    period="anual",
))

# Then use it like any built-in survey
INEIFetcher("enniv", years=range(2000, 2010)).fetch_modules().download().organize()
```

---

## Example 6 — RENAMU, full download

```python
from perustats.inei import INEIFetcher

(INEIFetcher("renamu", years=range(2012, 2024), parallel_jobs=4)
    .fetch_modules()
    .download()                        # no module_codes = download all
    .organize(organize_by="year"))
```

---

## Tips & Best Practices

- **Start small**: test with one or two years before requesting a full decade.
- **Use `force=False`**: skip already-downloaded files on re-runs to avoid redundant network traffic.
- **Tune `parallel_jobs`**: `4`–`6` workers usually gives the best throughput without overwhelming the INEI server.
- **Keep ZIPs initially**: set `remove_zip_after_extract=False` while experimenting; delete later once you confirm the extraction is complete.
- **Hash deduplication**: leave `deduplicate_docs_by_hash=True` (default) to avoid accumulating hundreds of identical PDF copies in the documentation folder.
