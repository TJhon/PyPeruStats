# Survey Registry

The `registry` object is the single source of truth for all known INEI surveys. It ships with five built-in surveys and can be extended at runtime without modifying any source files.

```python
from perustats.inei import registry, Survey
```

---

## Built-in Surveys

| Code | Full Name | Period |
|------|-----------|--------|
| `enaho` | Condiciones de Vida y Pobreza - ENAHO | Annual |
| `enaho_panel` | Condiciones de Vida y Pobreza - ENAHO Panel | Panel |
| `enapres` | Encuesta Nacional de Programas Presupuestales - ENAPRES | Annual |
| `endes` | Encuesta Demográfica y de Salud Familiar - ENDES | Annual |
| `renamu` | Registro Nacional de Municipalidades - RENAMU | Annual |

---

## `SurveyRegistry` API

### `list_codes()`

```python
registry.list_codes(period=None) -> list[str]
```

Returns all registered survey codes, sorted alphabetically. Pass `period="anual"` or `period="panel"` to filter.

```python
registry.list_codes()
# ['enaho', 'enaho_panel', 'enapres', 'endes', 'renamu']

registry.list_codes(period="panel")
# ['enaho_panel']
```

### `get()`

```python
registry.get(code: str) -> Survey
```

Returns the `Survey` object for `code`. Raises `KeyError` with a helpful message if the code is not found.

```python
survey = registry.get("endes")
print(survey)
# endes (anual): Encuesta Demográfica y de Salud Familiar - ENDES
```

### `register()`

```python
registry.register(survey: Survey) -> SurveyRegistry
```

Registers a new survey. Returns the registry itself for chaining. Raises `ValueError` if the code is already registered.

### `all()`

```python
registry.all() -> list[Survey]
```

Returns all registered `Survey` instances.

---

## `Survey` Dataclass

```python
@dataclass(frozen=True)
class Survey:
    code: str         # short identifier, e.g. "enaho"
    name: str         # full Spanish name as used in the INEI portal
    period: str       # "anual" or "panel"
```

---

## Adding a New Survey

Registering a survey that is not built in requires only one call:

```python
from perustats.inei import registry, Survey

registry.register(Survey(
    code="enniv",
    name="Encuesta Nacional de Niveles de Vida",
    period="anual",
))
```

After this, the new code is usable everywhere:

```python
from perustats.inei import INEIFetcher

fetcher = INEIFetcher("enniv", years=range(2010, 2020))
fetcher.fetch_modules().download().organize()
```

!!! warning "Persistence"
    Registrations made at runtime are **not** persisted between Python sessions. Place your `registry.register(...)` call in your project's initialization module if you need it consistently available.
