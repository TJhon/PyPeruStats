# 📊 Scraper ONPE – Resultados Electorales

Este proyecto permite descargar resultados electorales a nivel de **distrito (ubigeo)** desde el backend de la ONPE.

El flujo consta de dos etapas:

1. Obtener la estructura de ubigeos (departamento → provincia → distrito)
2. Descargar resultados electorales por cada distrito

---

## 🚀 Uso rápido

### 1. Generar ubigeos (solo la primera vez)

```bash
python ubigeo.py
```

Esto generará:

```
data/onpe/distritos_ubigeos.json
```

---

### 2. Descargar resultados

```bash
python resultados.py
```

Este script:

- Lee los ubigeos generados
- Consulta los endpoints de ONPE
- Guarda resultados por distrito

---

## 📁 Estructura del proyecto

```
.
├── ubigeo.py
├── resultados.py
├── data/
│   └── onpe/
│       ├── cache/
│       ├── distritos_ubigeos.json
│       └── result/
│           └── {fecha}/
│               └── {departamento}/
│                   └── {ubigeo}.json
```

---

## 📦 Estructura de datos

Cada archivo generado contiene:

```json
{
  "totales": {...},
  "resultados": [...],
  "ubigeo": {...},
  "actualizacion": "YYYY-MM-DD HH"
}
```

### 🔹 `totales`

Información agregada del distrito:

- Actas contabilizadas
- Participación ciudadana
- Total de votos

### 🔹 `resultados`

Lista de candidatos:

- Partido político
- Nombre del candidato
- Votos obtenidos
- Porcentajes

### 🔹 `ubigeo`

Parámetros usados en la consulta

---

## ⚙️ Configuración

En `ubigeo.py`:

```python
ID_ELECCION = 10
```

Puedes cambiarlo según el proceso electoral que necesites.

---

## ⚡ Características

- ✅ Descarga jerárquica: departamento → provincia → distrito
- ✅ Uso de caché para evitar requests repetidos
- ✅ Descarga incremental (no sobrescribe archivos existentes)
- ✅ Organización por fecha de ejecución
- ✅ Tolerancia a errores (continúa si falla un distrito)

---

## ⚠️ Consideraciones

- El script depende de endpoints públicos de ONPE (pueden cambiar)
- Se usa un `timeout=2`, lo que puede generar fallos en conexiones lentas
- Se recomienda ejecutar varias veces para completar datos faltantes

---

## 🛠 Dependencias

```bash
pip install requests pandas tqdm
```

---

## 📌 Notas

- El scraping se realiza directamente desde:

  ```
  https://resultadoelectoral.onpe.gob.pe/presentacion-backend
  ```

- Los datos se guardan en formato JSON para facilitar su análisis posterior.
