# Step Primitives

Steps are the building blocks of a MEF workflow. You pass a **flat list** of step objects to `MEFScraper`, and the internal `Workflow` parser groups them into structured `Step` records.

```python
from perustats.MEF.steps.click import Rows, ClickBtn, Search, SavePartial
```

---

## The Flat-List Convention

Steps are written as alternating `Rows → ClickBtn` pairs, with optional `Search` and `SavePartial` inserted between them:

```python
steps = [
    Rows([...]),       # which rows to act on
    ClickBtn(...),     # which button to click
    Search(...),       # optional: search filter after click
    SavePartial(...),  # optional: checkpoint save

    Rows([...]),       # next level
    ClickBtn(...),
    ...
]
```

The parser groups everything between two `Rows` instances into one `Step`. Every `Rows` **must** be followed by a `ClickBtn` — the parser raises `ValueError` otherwise.

---

## `Rows`

```python
@dataclass
class Rows:
    rows: list[str] = []
    on_missing: OnMissing = OnMissing.RECORD
```

Filters which rows of the current table will be visited before clicking the next button. Matching is **case-insensitive regex** — each string in `rows` is tested as a pattern against the row's text content.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rows` | `list[str]` | `[]` | Regex fragments. A row matches if **any** fragment is found in its text. An empty list matches **all** rows. |
| `on_missing` | `OnMissing` | `RECORD` | Behavior when a pattern matches no rows. See `OnMissing` below. |

### Examples

```python
Rows(["total"])                     # only the "Total" row
Rows(["ica", "junin", "piura"])     # three specific departments
Rows(["bienes y servicios"])        # any row containing this phrase
Rows()                              # all rows (iterate everything)
```

---

## `ClickBtn`

```python
@dataclass
class ClickBtn:
    button: str
    as_column: bool = True
    name: str  # auto-generated from button
```

Simulates clicking a drill-down button on the MEF portal. Use the constants in `perustats.MEF.constants.buttons` (imported as `BTN`) instead of hardcoding strings.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `button` | `str` | — | The button's HTML `name` attribute. Use `BTN.*` constants. |
| `as_column` | `bool` | `True` | If `True`, the value of each visited row is added as a metadata column to the final DataFrame. Set `False` to navigate through a level silently. |
| `name` | `str` | *auto* | Column name derived from the button string (everything after `"Btn"`). You can override this at instantiation if needed. |

### Examples

```python
ClickBtn(BTN.NIVEL_GOBIERNO)                        # adds "TipoGobierno" column
ClickBtn(BTN.GOB_LOCALES_MANCOMUNIDADES, as_column=False)  # navigate silently
ClickBtn(BTN.DEPARTAMENTO)                          # adds "Departamento" column
```

---

## `Search`

```python
@dataclass
class Search:
    query: str = None
    method: Literal["description", "code"] = "description"
```

Used when a table has more than ~400 rows and the MEF portal activates its server-side search panel. Insert `Search` **after** a `ClickBtn` (before the next `Rows`) to filter the table via the MEF backend before row iteration begins.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | `None` | The search text to send to the MEF search panel. |
| `method` | `"description"` \| `"code"` | `"description"` | Whether to search by row description text or by numeric code. |

### Example

```python
steps = [
    ...
    Rows(["locales"]),
    ClickBtn(BTN.MUNICIPALIDAD),
    Search("provincial"),       # filters large municipality table server-side
    Rows(["lima"]),
    ClickBtn(BTN.GENERICA),
]
```

!!! note
    `Search` is a no-op if the current table does not have a search panel — `MEFScraper` checks for panel presence before sending the search request.

---

## `SavePartial`

```python
@dataclass
class SavePartial:
    filename_prefix: str | None = None
```

!!! warning "Not yet implemented"
    `SavePartial` is defined and parsed but **not yet active**. It is reserved for a future checkpoint feature that will write partial results to disk after each row iteration at this step, making long scrapes resilient to MEF portal downtime.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filename_prefix` | `str \| None` | `None` | Prefix for checkpoint filenames. `None` disables saving. |

---

## `OnMissing` Enum

```python
class OnMissing(str, Enum):
    SKIP   = "skip"
    RECORD = "record"   # default
    RAISE  = "raise"
```

Controls what happens when a `Rows` filter pattern matches no rows in the table:

| Value | Behavior |
|-------|----------|
| `SKIP` | Silently ignore this step iteration. |
| `RECORD` | Record the miss internally (default; useful for debugging). |
| `RAISE` | Raise an exception immediately. |

---

## `Workflow` — The Parser

You never need to call `Workflow` directly — `MEFScraper` does it for you. But it is useful to instantiate it standalone to **inspect** or **debug** how your flat step list is being interpreted:

```python
from perustats.MEF.steps.workflow import Workflow

wk = Workflow(steps)
print(wk.p_steps)  # list[Step]
```

`Workflow._parse()` iterates the flat list, groups each `Rows → ClickBtn [Search] [SavePartial]` block into a `Step`, and raises `ValueError` if the structure is malformed.

### `Step` dataclass

```python
@dataclass
class Step:
    rows: Rows
    click: ClickBtn
    save: SavePartial | None = None
    search: Search | None = None
```

Each `Step` encodes one level of drill-down navigation.
