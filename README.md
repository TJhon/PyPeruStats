# PyPeruStats

Allows downloading data from various data sources in Peru.

Sources: INEI, BCRP

### Installation

```bash
pip install pyperustats
```



## INEI

### Parameters Description

#### MICRODATOS_INEI

- `survey`: Survey type ('enaho', 'enapres', 'endes')
  - Available up to 2024-Quarter 3

#### download_default

- `format`: Output file format
  - 'csv': CSV files
  - 'stata': Stata files
  - 'spss': SPSS files
- `force`: Force re-download of existing files
- `remove_zip`: Remove ZIP files after extraction
- `workers`: Number of workers for parallel download
- `zip_dir`: Directory to store ZIP files

#### organize_files

- `dir_output`: Directory where organized files will be saved
- `order_by`: Organization method
  - 'modules': Structure "mod_01/year_n.csv"
- `ext_documentation`: List of documentation extensions
- `delete_master_dir`: Delete master directory after organizing

### USAGE

```py
from pyPeruStats import MICRODATOS_INEI, print_tree

# Options: enaho, enapres, endes, available up to 2024-Quarter 3
enaho = MICRODATOS_INEI(survey="enaho") 
modules = enaho.modules
# Found modules 
print(modules.head(2))
```

```
   codigo_modulo                                      modulo      anio
0              1  Características de la Vivienda y del Hogar  2024 ...
1              2   Características de los Miembros del Hogar  2024 ...
```

```py
downloaded = enaho.search(
    [2021, 2023, 2004, 2006, 2007, 2008], [1, 2, 3, 8]
).download_default(
    format='csv', # csv, stata, spss
    force=False, # download zip files again
    remove_zip=False, # remove original zips from microdata page
    workers=4,  # Parallel download
    zip_dir="trash_zips" # where zips will be downloaded
)

# Downloaded files within directory
print_tree('./trash_zips/')
```

```
📁 trash_zips
└── 📁 inei_enaho_download
    ├── 📁 2004
        ├── 📁 2004_01
        │   └── 📁 280-Modulo01
        │   │   ├── 📄 CED-01-100 2004.pdf
        │   │   ├── 📄 Diccionario.pdf
        │   │   ├── 📄 enaho01-2004-100.dta
        │   │   └── 📄 Ficha Tecnica - 2004.pdf
        ├── 📁 2004_02
....
```

```py
result_files = downloaded.organize_files(
    dir_output="./data_inei/", # Where files will be saved
    order_by="modules", # modules: file structure "mod_01/year_n.csv" ; # year: file structure year_n/mod_n
    ext_documentation=['pdf'], # files used for documentation
    delete_master_dir=False # true if you want to delete all zip files and unzip again (use with caution)
)
print_tree("./data_inei/") # print file structure
```

```
📁 data_inei
├── 📁 documentation_pdf
    ├── 📄 2004_01_ced-01-100_2004.pdf
    ├── 📄 2004_01_diccionario.pdf
    ├── 📄 2004_01_ficha_tecnica_-_2004
...
└── 📁 modules
    ├── 📁 001
        ├── 📄 2004.dta
        ├── 📄 2006.dta
        ├── 📄 2007.dta
        ├── 📄 2008.csv
        ├── 📄 2021.csv
        └── 📄 2023.csv
    ├── 📁 002
        ├── 📄 2004.dta
        ├── 📄 2006.dta
        ├── 📄 2007.dta
        ├── 📄 2008.csv
....
```

### Notes

1. Parallel download significantly improves performance but consumes more resources
2. It's recommended to keep original ZIP files as backup
3. Check disk space before downloading multiple years/modules
4. Documentation files are organized in a separate directory


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

# TODO

- BCRP
  - [x] Download statistical data from BCRP
  - [ ] Implement advanced data search functionality
  - [ ] Create autoplot functionality (inspired by ggplot)
  - [ ] Set up GitHub repository and backup mechanism
  - [ ] Add comprehensive documentation
  - [ ] Create example notebooks