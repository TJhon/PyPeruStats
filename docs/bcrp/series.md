# BCRPSeries

`BCRPSeries` is a lightweight dataclass that describes a batched BCRP API query. It groups codes by frequency and pre-computes the date strings expected by each endpoint.

---

## Class signature

```python
@dataclass
class BCRPSeries:
    codes: list[str]
    start_date: str
    end_date: str
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `codes` | `list[str]` | One or more BCRP series codes. Leading/trailing whitespace is stripped automatically. Codes are normalised to uppercase. |
| `start_date` | `str` | Start of the date range in `YYYY-MM-DD` format. |
| `end_date` | `str` | End of the date range in `YYYY-MM-DD` format. |

### Raises

| Exception | When |
|---|---|
| `ValueError` | `codes` is an empty list |

---

## How frequency is inferred

The last character of each code is its frequency indicator:

| Suffix | Frequency | API date format |
|---|---|---|
| `D` | Daily | `YYYY-MM-DD` |
| `M` | Monthly | `YYYY-MM` |
| `Q` | Quarterly | `YYYY-{1-4}` |
| `A` | Annual | `YYYY` |

`BCRPSeries.__post_init__` groups the supplied codes by their suffix and converts `start_date` / `end_date` to the correct API format for each group.

---

## Computed attributes

After construction these attributes are available:

| Attribute | Type | Description |
|---|---|---|
| `freq_codes` | `dict[str, list[str]]` | Codes grouped by frequency, e.g. `{"D": ["RD16085DA"], "M": ["PD04657MD"]}` |
| `date_limits` | `dict[str, dict]` | Per-frequency start/end dates formatted for the API, e.g. `{"D": {"start_date": "2020-01-01", "end_date": "2024-12-31"}, "M": {"start_date": "2020-01", "end_date": "2024-12"}}` |

---

## Example

```python
from perustats.BCRP.models import BCRPSeries

series = BCRPSeries(
    codes=["RD16085DA", "PD04657MD", "RD15478DQ"],
    start_date="2018-01-01",
    end_date="2023-12-31",
)

print(series.freq_codes)
# {'A': ['RD16085DA'], 'M': ['PD04657MD'], 'Q': ['RD15478DQ']}

print(series.date_limits)
# {
#   'A': {'start_date': '2018', 'end_date': '2023'},
#   'M': {'start_date': '2018-01', 'end_date': '2023-12'},
#   'Q': {'start_date': '2018-1', 'end_date': '2023-4'},
# }
```

---

## Supported frequency aliases

When building codes manually, the canonical suffix characters are the only valid identifiers. The string aliases below (`"daily"`, `"monthly"`, etc.) are accepted by helper functions elsewhere in the library but **not** by the code suffix itself.

| Alias | Canonical |
|---|---|
| `"daily"` / `"d"` | `D` |
| `"monthly"` / `"m"` | `M` |
| `"quarterly"` / `"q"` | `Q` |
| `"yearly"` / `"annual"` / `"a"` | `A` |

---

## Default start date

The constant `DEFAULT_START_DATE = "1990-01-02"` is available from `perustats.BCRP.models` as a convenient lower bound for long historical pulls:

```python
from perustats.BCRP.models import BCRPSeries, DEFAULT_START_DATE
from datetime import date

series = BCRPSeries(
    codes=["CD10401DA"],
    start_date=DEFAULT_START_DATE,
    end_date=date.today().isoformat(),
)
```
