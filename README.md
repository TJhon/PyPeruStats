# PyPeruStats

Allows downloading data from various data sources in Peru.

Sources: INEI, BCRP

### Installation

```bash
pip install perustats
```



## INEI Microdata

### Overview

The `MicrodatosINEIFetcher` class provides a comprehensive tool for downloading and organizing INEI (Instituto Nacional de Estadística e Informática) microdata from Peruvian surveys.

### Key Features

- Fetch available modules across multiple years
- Download data files in multiple formats (Stata, SPSS, CSV, DBF)
- Parallel downloading with configurable workers
- Automatic ZIP extraction and validation
- Flexible file organization by module or year
- Smart documentation handling with duplicate detection
- Hash-based deduplication for PDF files

### Parameters

#### `MicrodatosINEIFetcher`

- `survey`: Survey type to fetch
  - `'enaho'`: National Household Survey
  - `'endes'`: Demographic and Family Health Survey
  - `'enapres'`: National Budget Programs Survey
  - Available up to 2024
  
- `years`: List of years to fetch data for (e.g., `[2020, 2021, 2022]`)

- `master_directory`: Root directory for storing downloaded data (default: `'./microdatos_inei'`)

- `parallel_jobs`: Number of parallel download jobs (default: `2`)

#### `download_zips()`

- `formats`: List of formats to download (default: `['stata', 'spss', 'csv']`)
  - `'stata'`: Stata .dta files
  - `'spss'`: SPSS .sav files
  - `'csv'`: CSV files
  - `'dbf'`: dBASE files

- `force_download`: Force re-download even if file exists (default: `True`)

- `module_codes`: List of specific module codes to download (empty list = download all)

- `remove_zip_after_extract`: Delete ZIP files after extraction (default: `False`)

#### `organize_files()`

- `organize_by`: Organization scheme
  - `'module'`: Structure by module (e.g., `001_module_name/2020_file.csv`)
  - `'year'`: Structure by year (e.g., `2020/001_file.csv`)

- `keep_original_names`: Keep original filenames (default: `True`)

- `operation`: File operation type
  - `'copy'`: Copy files (preserves originals)
  - `'move'`: Move files (removes from unzipped directory)

- `docs_by_hash`: Use hash-based deduplication for documentation files (default: `True`)
  - When `True`, identical PDFs are stored only once regardless of filename

### Usage Examples

#### Example 1: ENDES Survey (Multiple Years and Modules)

```python
from perustats import MicrodatosINEIFetcher
import time

# Initialize ENDES fetcher for years 1990-2023
start = time.time()
endes = MicrodatosINEIFetcher(
    survey="endes",
    years=list(range(1990, 2024)),
    master_directory="./datos_inei",
    parallel_jobs=6
)

# Fetch available modules
endes.fetch_modules()

# Download specific modules in multiple formats
endes.download_zips(
    formats=["spss", "dbf", "stata", "csv"],
    module_codes=[64, 65, 73, 74],  # Specific modules
    force_download=True,
    remove_zip_after_extract=False
)

# Organize files by year
endes.organize_files(
    organize_by="year",
    keep_original_names=True,
    operation="copy"
)

# Also organize by module
endes.organize_files(
    organize_by="module",
    keep_original_names=True,
    operation="copy"
)

```

#### Example 2: ENAHO Survey (National Household Survey)

```python
# Initialize ENAHO fetcher for years 2000-2024
enaho = MicrodatosINEIFetcher(
    survey="enaho",
    years=list(range(2000, 2025)),
    master_directory="./datos_inei",
    parallel_jobs=4
)

# Fetch available modules
enaho.fetch_modules()

# Display available modules (first 5)
print(enaho.modules_dataframe.head())

# Download specific modules
enaho.download_zips(
    formats=["csv", "stata", "spss", "dbf"],
    module_codes=[1, 13, 22, 34],
    force_download=False
)

# Organize by year with original names
enaho.organize_files(
    organize_by="year",
    keep_original_names=True,
    operation="copy",
    docs_by_hash=True  # Deduplicate documentation by content hash
)

# Also organize by module
enaho.organize_files(
    organize_by="module",
    keep_original_names=True,
    operation="copy"
)
```

#### Example 3: ENAPRES Survey (Budget Programs)

```python
# Initialize ENAPRES fetcher
enapres = MicrodatosINEIFetcher(
    survey="enapres",
    years=list(range(2010, 2025)),
    master_directory="./datos_inei",
    parallel_jobs=3
)

# Fetch and download in one chain
enapres.fetch_modules().download_zips(
    formats=["stata", "csv"],
    module_codes=[101, 102, 111]
).organize_files(
    organize_by="module",
    keep_original_names=True,
    operation="move"  # Move instead of copy to save space
)
```

#### Example 4: Inspect Available Modules

```python
# Fetch modules without downloading
enaho = MicrodatosINEIFetcher(
    survey="enaho",
    years=[2020, 2021, 2022, 2023]
)

enaho.fetch_modules()

# View available modules
print(enaho.modules_dataframe[['year', 'module_code', 'module_name']])
```

### Directory Structure

The fetcher creates the following directory structure:

```
./microdatos_inei/
└── enaho/                          # Survey name
    ├── 0_zips/                     # Downloaded ZIP files
    │   ├── 2020_mod_001.zip
    │   └── 2020_mod_002.zip
    ├── 1_unzipped/                 # Extracted contents
    │   ├── 2020_mod_001/
    │   └── 2020_mod_002/
    └── 2_organized/                # Organized files
        ├── by_module/              # When organize_by='module'
        │   ├── 001_vivienda_hogar/
        │   │   ├── 2020_file.csv
        │   │   └── 2021_file.csv
        │   └── 002_caracteristicas_miembros/
        │       ├── 2020_file.csv
        │       └── 2021_file.csv
        ├── by_year/                # When organize_by='year'
        │   ├── 2020/
        │   │   ├── 001_file.csv
        │   │   └── 002_file.csv
        │   └── 2021/
        │       ├── 001_file.csv
        │       └── 002_file.csv
        └── documentation/          # PDF documentation (deduplicated)
            ├── 2020_mod_001_manual.pdf
            └── 2020_mod_002_manual.pdf
```

### Important Attributes

- `modules_dataframe`: DataFrame containing all available modules for the specified years
- `documentation_map`: Dictionary mapping canonical PDF filenames to their aliases (useful for tracking deduplicated files)
- `zip_maps`: List of tuples containing (zip_path, extract_path) for all processed files

### Best Practices

1. **Start with fewer years**: Test with 2-3 years before downloading extensive ranges
2. **Use parallel jobs wisely**: Higher values speed up downloads but consume more bandwidth
3. **Keep ZIP files initially**: Set `remove_zip_after_extract=False` for backup purposes
4. **Hash-based deduplication**: Enable `docs_by_hash=True` to avoid duplicate documentation files
5. **Check disk space**: Large surveys across many years can consume significant storage
6. **Use method chaining**: The fluent API allows chaining `fetch_modules()`, `download_zips()`, and `organize_files()`

### Performance Tips

- Use `parallel_jobs=4` or higher for faster downloads (adjust based on your connection)
  - With 100 Mbps connection: ~134 ZIP files download in 1.20-1.30 seconds
- Use `operation='move'` instead of `'copy'` to save disk space
- Filter by `module_codes` to download only needed modules
- Enable `remove_zip_after_extract=True` if storage is limited (after verifying extraction)

### Notes

- ZIP file integrity is automatically validated; corrupted files are re-downloaded
- Documentation files are deduplicated by content hash when `docs_by_hash=True`
- The class handles network failures gracefully with automatic retries
- All file operations preserve original data integrity


## BCRP

### Current Issues with the Source Data

1. Inconsistent Data Formats Across Frequencies
   - **Spanish Month Abbreviations**  
     For example: `"Ene05"` (January 2005 in Spanish format).  
   - **Complex Date Strings**  
     Example: `"31Ene05"` combines day, month (abbreviated in Spanish), and year, requiring parsing.  
   - **Quarterly Indicators**  
     Example: `"T113"` indicates the 1st quarter of 2013 and needs transformation to a standard format.  

2. Additional Steps Required for Proper DataFrame Conversion
   - Converting non-standard date strings to a format recognized by `pandas` or similar libraries.  
   - Harmonizing date formats across daily, monthly, quarterly, and annual frequencies.  

3. Slow Response Time from the BCRP UI
   - The platform often experiences delays when fetching data, impacting the efficiency of workflows.  


### Features

- Seamless data retrieval across different time frequencies
- Automatic conversion of Spanish date formats to standard datetime
- Parallel processing capabilities
- Built-in caching mechanism
- Flexible data processing



```py
from pyPeruStats import BCRPDataProcessor

# Define series codes
diarios = ["PD38032DD", "PD04699XD"]
mensuales = ["RD38085BM", "RD38307BM"]
trimestrales = ["PD37940PQ", "PN38975BQ"]
anuales = [
    "PM06069MA",
    "PM06078MA",
    "PM06101MA",
    "	PM06088MA",
    "PM06087MA",
    "	PM06086MA",
    "	PM06085MA",
    "	PM06084MA",
    "	PM06083MA",
    "	PM06082MA",
    "	PM06081MA",
    "	PM06070MA",
]

# Combine all frequencies
all_freq = diarios + mensuales + trimestrales + anuales

# Initialize processor
processor = BCRPDataProcessor(
    all_freq, 
    start_date="2002-01-02", 
    end_date="2023-01-01", 
    parallel=True
)

# Process data
data = processor.process_data(save_sqlite=True)

# Access DataFrames by frequency
anuales_df = data.get("A")
trimestrales_df = data.get("Q")
mensuales_df = data.get("M")
diarios_df = data.get("D")
```



### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### License

Apache 2.0

### Contact

fr.jhonk@gmail.com

