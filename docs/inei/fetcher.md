# INEIFetcher Reference

`INEIFetcher` is the main entry-point class for the INEI microdata module.

```python
from perustats.inei import INEIFetcher
```

---

## Constructor

```python
INEIFetcher(
    survey,
    years,
    master_directory="./data/",
    inei_directory="microdatos_inei",
    parallel_jobs=2,
    preferred_formats=None,
    sql_file=None,
)
```

### Parameters

| Parameter           | Type                | Default                        | Description                                                                                  |
| ------------------- | ------------------- | ------------------------------ | -------------------------------------------------------------------------------------------- |
| `survey`            | `str`               | —                              | Survey code. Must be registered in the `registry` (e.g. `"enaho"`, `"endes"`).               |
| `years`             | `Iterable[int]`     | —                              | Years to fetch. Accepts any iterable — `range`, list, etc.                                   |
| `master_directory`  | `str`               | `"./data/"`                    | Root directory for all downloaded and processed files.                                       |
| `inei_directory`    | `str`               | `"microdatos_inei"`            | Subdirectory inside `master_directory` used to organize INEI data.                           |
| `parallel_jobs`     | `int`               | `2`                            | Number of concurrent download threads.                                                       |
| `preferred_formats` | `list[str] \| None` | `["stata","spss","csv","dbf"]` | Ordered format preference. The first format with a valid URL for a given module is selected. |
| `sql_file`          | `str \| None`       | `"referrer.db"`                | Path (relative to `master_directory`) for the SQLite progress/cache database.                |

!!! tip

    If you have a stable internet connection and fast storage (e.g., SSD), you can increase the `parallel_jobs` parameter to improve download speed.

    For example, on my setup using an HDD and `parallel_jobs=6`, I was able to download 146 ZIP files in approximately 30 secs.

### Raises

- `KeyError` — if `survey` is not found in the registry. Call `registry.list_codes()` to see valid codes.

---

## Methods

### `fetch_modules()`

```python
fetcher.fetch_modules() -> INEIFetcher
```

Retrieves (or loads from the SQLite cache) the module listing for every requested year.

**Returns** `self` for method chaining.

After this call, `fetcher.modules_df` is populated with a `pandas.DataFrame` containing one row per (year, module) combination, including download URLs and local paths.

!!! note "Caching"

    Module listings are cached in the SQLite database. Re-running `fetch_modules()` on the same years will not hit the network a second time.

---

### `download()`

```python
fetcher.download(
    module_codes=None,
    force=False,
    remove_zip_after_extract=False,
) -> INEIFetcher
```

Downloads and extracts ZIP files for the modules returned by `fetch_modules()`.

**Parameters**

| Parameter                  | Type                | Default | Description                                                                      |
| -------------------------- | ------------------- | ------- | -------------------------------------------------------------------------------- |
| `module_codes`             | `list[int] \| None` | `None`  | Restrict download to these module codes. `None` downloads all available modules. |
| `force`                    | `bool`              | `False` | Re-download even if a valid ZIP already exists on disk.                          |
| `remove_zip_after_extract` | `bool`              | `False` | Delete each ZIP file after successful extraction.                                |

**Returns** `self` for method chaining.

**Raises**

- `RuntimeError` — if called before `fetch_modules()`.
- `TypeError` — if `module_codes` is not a list/tuple/set or `None`.

!!! tip "Filtering modules"

    Module codes are zero-padded 4-digit strings internally (e.g. `1` → `"0001"`). You can pass plain integers like `[1, 2, 13]` and they will be converted automatically.

---

### `organize()`

```python
fetcher.organize(
    organize_by="module",
    keep_original_names=True,
    operation="copy",
    deduplicate_docs_by_hash=True,
) -> INEIFetcher
```

Moves or copies extracted files from `1_unzipped/` into a clean directory tree under `2_organized/`.

**Parameters**

| Parameter                  | Type                 | Default    | Description                                                           |
| -------------------------- | -------------------- | ---------- | --------------------------------------------------------------------- |
| `organize_by`              | `"module" \| "year"` | `"module"` | Directory grouping scheme.                                            |
| `keep_original_names`      | `bool`               | `True`     | Preserve original filenames.                                          |
| `operation`                | `"copy" \| "move"`   | `"copy"`   | Whether to copy files (preserving originals) or move them.            |
| `deduplicate_docs_by_hash` | `bool`               | `True`     | Deduplicate documentation files (PDFs, etc.) by SHA-256 content hash. |

**Returns** `self` for method chaining.

**Raises**

- `RuntimeError` — if called before `fetch_modules()`.

---

## Attributes

| Attribute    | Type                       | Description                                                              |
| ------------ | -------------------------- | ------------------------------------------------------------------------ |
| `modules_df` | `pandas.DataFrame \| None` | Module catalogue populated by `fetch_modules()`. `None` before the call. |
| `survey`     | `Survey`                   | The resolved `Survey` dataclass instance.                                |
| `years`      | `list[int]`                | Years passed to the constructor.                                         |
| `db`         | `DatabaseManager`          | SQLite manager used for caching and progress tracking.                   |

### `modules_df` columns

| Column          | Description                                    |
| --------------- | ---------------------------------------------- |
| `year_ref`      | Survey year                                    |
| `module_code`   | Zero-padded 4-digit module identifier          |
| `module_name`   | Human-readable module name                     |
| `spss`          | Download URL for SPSS format (if available)    |
| `stata`         | Download URL for Stata format (if available)   |
| `csv`           | Download URL for CSV format (if available)     |
| `dbf`           | Download URL for dBASE format (if available)   |
| `url`           | Resolved URL based on `preferred_formats`      |
| `path_download` | Absolute path where the ZIP will be saved      |
| `path_extract`  | Absolute path where the ZIP will be extracted  |
| `downloaded`    | `bool` — whether the ZIP has been downloaded   |
| `unzipped`      | `bool` — whether the ZIP has been extracted    |
| `organized`     | `bool` — whether the files have been organized |

---

## Full Example

```python
from perustats.inei import INEIFetcher

fetcher = INEIFetcher(
    survey="enaho",
    years=range(2018, 2024),
    master_directory="./datos",
    parallel_jobs=6,
)

fetcher.fetch_modules()

# Inspect what is available
print(fetcher.modules_df[["year_ref", "module_code", "stata"]].dropna())

# Download a subset of modules
fetcher.download(module_codes=[1, 2, 5, 13, 22], force=False)

# Organize by year, then by module
fetcher.organize(organize_by="year", operation="copy")
fetcher.organize(organize_by="module", operation="copy")
```
