# PyPeruStats

Allows downloading data from various data sources in Peru.

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

### Installation

```bash
pip install pyperustats
```


```py
from PeruStats import BCRPDataProcessor

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