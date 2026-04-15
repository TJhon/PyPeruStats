# TODO — MEF Module Roadmap

Planned features and improvements for the `perustats.MEF` module.

---

## 🔜 In Progress / Next Up

### Progress Bars

Add rich visual feedback during long-running scrapes using the `rich` library's progress utilities.

- [ ] Step-level progress bar showing `Step N / Total` as each navigation level is entered
- [ ] Row-level progress bar within each step showing `Row N / M (current_value)`
- [ ] Display the current metadata context (year, filters applied) in the progress description
- [ ] Configurable verbosity: `verbose=False` to silence all output, `verbose=True` (default) for progress bars
- [ ] Nested progress bars for multi-level workflows using `rich.progress.Progress` with `TaskID`

```python
# Planned API (subject to change)
MEFScraper(steps, verbose=True).run(2023)
# ↓
# Scraping MEF gasto 2023 ━━━━━━━━━━━━━━━━━━━━━━ 100% Step 3/4
#   TipoGobierno → Locales  ━━━━━━━━━━━━━━━━━━━━━ 100% Row 2/2
#   Departamento            ━━━━━━━━━━━━━━━━━╸━━━  72% Row 18/25
```

---

### Partial Saves (`SavePartial`)

`SavePartial` is already parsed and accepted in the step list but is not yet active. Implementation will:

- [ ] Write a Parquet or CSV checkpoint after completing all row iterations at the marked step
- [ ] Detect existing checkpoints on startup and skip already-scraped rows
- [ ] Allow resuming an interrupted scrape without restarting from zero
- [ ] Expose a `resume=True` flag on `MEFScraper.run()` to opt into checkpoint recovery

```python
# Planned behavior
steps = [
    ...
    Rows(),
    ClickBtn(BTN.DEPARTAMENTO),
    SavePartial(filename_prefix="departamento"),  # will checkpoint here
    ...
]
MEFScraper(steps, master_dir_save="./data/mef/").run(2023)
# If interrupted and re-run, already-saved departments are skipped
```

---

## 📋 Planned Features

### Async / Concurrent Requests

- [ ] `asyncio`-based HTTP requests to parallelize row iterations at each step
- [ ] Configurable concurrency limit (`max_workers`) to avoid overwhelming the MEF server
- [ ] Estimated time remaining based on rows completed

### `OnMissing` Full Implementation

- [ ] `OnMissing.SKIP` — silently skip steps where no row matches the filter
- [ ] `OnMissing.RAISE` — raise `ValueError` on missing rows (useful for strict pipelines)
- [ ] `OnMissing.RECORD` — log misses to a `scraper.missing` attribute for post-run inspection

### Retry Logic

- [ ] Automatic retry with exponential backoff for network errors and MEF 500 responses
- [ ] Configurable `max_retries` and `retry_delay` parameters on `MEFScraper`

### Output Formats

- [ ] `.save()` method to write results directly to CSV, Parquet, or Excel
- [ ] Optional column renaming / localization to Spanish descriptive names

### Extended Year Support

- [ ] Monitor MEF portal for v8 migration and update URL/column configs accordingly

---

## 🐛 Known Limitations

- The MEF portal is occasionally down or slow — no retry logic yet.
- `SavePartial` steps are parsed but do nothing at runtime.
- `OnMissing` enum is defined but not yet enforced in `_proces_step`.
- Very large result sets (all municipalities, all years) can be slow due to sequential HTTP requests.

---

## 💡 Ideas Under Consideration

- A `MEFScraper.preview()` method that simulates the first step offline and returns the initial table without making further requests.
- CLI entrypoint (`perustats mef run ...`) for one-off queries without writing a script.
- Integration with `perustats` caching layer (shared with BCRP module) to avoid redundant requests.
