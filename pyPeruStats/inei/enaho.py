import pandas as pd

from .utils import clean_names

enaho_metadata = 'https://raw.githubusercontent.com/TJhon/PyPeruStats/refs/heads/inei/MetadataSources/INEI/enaho_actualizado.csv'

metadata = pd.read_csv(enaho_metadata)

clean_names(metadata)

print(metadata.head())