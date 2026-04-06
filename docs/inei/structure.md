# Directory Structure

`INEIFetcher` creates a predictable, self-contained directory tree under `master_directory`. Understanding the layout helps when inspecting downloads or integrating with downstream pipelines.

---

## Full Layout

```
<master_directory>/
│
├── referrer.db                          # SQLite cache & progress database
│
└── microdatos_inei/                     # inei_directory (configurable)
    └── <survey>/                        # e.g. "enaho", "endes"
        │
        ├── 0_zips/                      # raw downloaded ZIP files
        │   ├── 2020_mod_0001.zip
        │   ├── 2020_mod_0002.zip
        │   └── ...
        │
        ├── 1_unzipped/                  # extracted ZIP contents
        │   ├── 2020_mod_0001/
        │   │   ├── enaho01-2020.dta
        │   │   └── ficha_tecnica.pdf
        │   └── ...
        │
        └── 2_organized/
            │
            ├── by_year/                 # organize_by="year"
            │   ├── 2020/
            │   │   ├── 0001_enaho01-2020.dta
            │   │   └── 0002_enaho02-2020.dta
            │   └── 2021/
            │       └── ...
            │
            ├── by_module/               # organize_by="module"
            │   ├── 0001_vivienda_hogar/
            │   │   ├── 2020_enaho01.dta
            │   │   └── 2021_enaho01.dta
            │   └── ...
            │
            └── documentation/           # deduplicated PDFs and docs
                ├── ficha_tecnica.pdf
                └── ...
```

---

## Stage Descriptions

### `0_zips/`

Holds the raw ZIP files downloaded from the INEI portal. Filenames follow the pattern `<year>_mod_<code>.zip`. ZIPs are validated after download; corrupted files are automatically re-fetched.

Set `remove_zip_after_extract=True` in `download()` to delete these after extraction and save disk space.

### `1_unzipped/`

Each ZIP is extracted into its own subdirectory named `<year>_mod_<code>/`. The original filenames inside the ZIP are preserved.

### `2_organized/`

This is the analysis-ready output. Files are placed in one or both of the two sub-schemes:

**`by_year/`** — groups every module for the same year together. Useful when you process one year at a time.

**`by_module/`** — groups all years for the same module together. Useful for longitudinal analysis.

**`documentation/`** — aggregates all documentation files (PDFs, DOC, PPT, XLS …) across years. When `deduplicate_docs_by_hash=True`, identical files are stored only once regardless of filename, eliminating the redundant copies that INEI typically ships with each year's ZIP.

---

## SQLite Database (`referrer.db`)

The database is created at `<master_directory>/referrer.db` (or a custom path via `sql_file`). It stores:

- **Module cache** — scraped module listings per survey and year, so `fetch_modules()` does not repeat network requests.
- **Progress flags** — `downloaded`, `unzipped`, `organized`, `removed_zip` booleans per module row, allowing interrupted workflows to resume cleanly.

You can inspect the database directly with any SQLite browser.
