# Button Constants

All MEF portal button IDs are defined in `perustats.MEF.constants.buttons`. Import the module as `BTN` by convention:

```python
from perustats.MEF.constants import buttons as BTN
```

Then reference buttons as `BTN.NIVEL_GOBIERNO`, `BTN.DEPARTAMENTO`, etc.

---

## Available Constants

These constants map to the HTML `name` attribute of each drill-down button in the MEF Consulta Amigable interface. You can find them by opening the portal in a browser, pressing F12, and hovering over a button to inspect its `name` property.

### Budget Structure

| Constant | Button ID | Description |
|----------|-----------|-------------|
| `BTN.GENERICA` | `ctl00$CPH1$BtnGenerica` | Generic expenditure category |
| `BTN.SUB_GENERICA` | `ctl00$CPH1$BtnSubGenerica` | Sub-generic expenditure category |
| `BTN.DETALLE_SUB_GENERICA` | `ctl00$CPH1$BtnSubGenericaDetalle` | Detail of sub-generic category |
| `BTN.ESPECIFICA` | `ctl00$CPH1$BtnEspecifica` | Specific expenditure item |
| `BTN.DETALLE_ESPECIFICA` | `ctl00$CPH1$BtnEspecificaDetalle` | Detail of specific item |

### Government Levels

| Constant | Button ID | Description |
|----------|-----------|-------------|
| `BTN.NIVEL_GOBIERNO` | `ctl00$CPH1$BtnTipoGobierno` | Top-level government type (Nacional, Regional, Local) |
| `BTN.SUB_TIPO_GOBIERNO` | `ctl00$CPH1$BtnSubTipoGobierno` | Sub-type of government |
| `BTN.GOB_LOCALES_MANCOMUNIDADES` | `ctl00$CPH1$BtnSubTipoGobierno` | Local governments / Mancomunidades *(alias of SUB_TIPO_GOBIERNO)* |

### Geography

| Constant | Button ID | Description |
|----------|-----------|-------------|
| `BTN.DEPARTAMENTO` | `ctl00$CPH1$BtnDepartamento` | Department (region) |
| `BTN.DEPARTAMENTO_META` | `ctl00$CPH1$BtnDepartamentoMeta` | Department by budget goal |
| `BTN.MUNICIPALIDAD` | `ctl00$CPH1$BtnMunicipalidad` | Municipality |

### Budget Programs & Functions

| Constant | Button ID | Description |
|----------|-----------|-------------|
| `BTN.FUNCION` | `ctl00$CPH1$BtnFuncion` | Budget function |
| `BTN.PROGRAMA` | `ctl00$CPH1$BtnPrograma` | Budget program |
| `BTN.SUB_PROGRAMA` | `ctl00$CPH1$BtnSubPrograma` | Sub-program |
| `BTN.PROGRAMA_PPTO` | `ctl00$CPH1$BtnProgramaPpto` | Programmatic budget category |
| `BTN.PROGRAMA_PARTICIPATIVO` | `ctl00$CPH1$BtnProgramaPpto` | Participatory budget program *(alias)* |
| `BTN.CATEGORIA_PRESUPUESTAL` | `ctl00$CPH1$BtnProgramaPpto` | Budget category *(alias)* |
| `BTN.ACTIVIDAD_PROYECTO` | `ctl00$CPH1$BtnActProy` | Activity / Project |
| `BTN.PRODUCTO_PROYECTO` | `ctl00$CPH1$BtnProdProy` | Product / Project |
| `BTN.ACTIVIDAD_ACCION` | `ctl00$CPH1$BtnAAO` | Activity / Action / Operation |

### Financing

| Constant | Button ID | Description |
|----------|-----------|-------------|
| `BTN.FUENTE` | `ctl00$CPH1$BtnFuenteAgregada` | Aggregated funding source |
| `BTN.RUBRO` | `ctl00$CPH1$BtnRubro` | Revenue heading (rubro) |

### Time

| Constant | Button ID | Description |
|----------|-----------|-------------|
| `BTN.MES` | `ctl00$CPH1$BtnMes` | Month |
| `BTN.TRIMESTRE` | `ctl00$CPH1$BtnTrimestre` | Quarter |

---

## Adding Custom Buttons

If you need a button not listed above, you can pass its raw ID string directly to `ClickBtn`:

```python
from perustats.MEF.steps.click import ClickBtn

ClickBtn("ctl00$CPH1$BtnSomeOtherButton")
```

To discover the button ID: open the MEF portal, press **F12**, hover over the button you want, and look for the `name` attribute in the HTML `<input>` or `<a>` element.

---

## Alias Map

Several constants share the same underlying button ID because the MEF portal reuses the same button across different navigation contexts:

| Aliases | Shared ID |
|---------|-----------|
| `GOB_LOCALES_MANCOMUNIDADES`, `SUB_TIPO_GOBIERNO` | `ctl00$CPH1$BtnSubTipoGobierno` |
| `PROGRAMA_PARTICIPATIVO`, `PROGRAMA_PPTO`, `CATEGORIA_PRESUPUESTAL` | `ctl00$CPH1$BtnProgramaPpto` |
