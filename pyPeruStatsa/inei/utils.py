import os, requests, zipfile
import pandas as pd
from unidecode import unidecode

TYPE_FILES_EXT = {"csv": ".csv", "spss": ".sav", "stata": ".dta", "pdf": ".pdf"}

TRASH = "./trash/"



def clean_names(df: pd.DataFrame):
    df.columns = [
        unidecode(c).lower().replace(" ", "_").replace(".", "_").strip()
        for c in df.columns
    ]
    df.rename(columns={"ano": "anio", "a_no": "anio"}, inplace=True)





def get_all_data_year(year, data, break_year=2006):
    df = data.copy()
    df_ref = df.query("anio == @year")
    is_spsss = year < break_year
    base_cols = ["anio", "codigo_modulo"]
    if is_spsss:
        ref_df = df_ref[base_cols + ["spss"]]
    else:
        ref_df = df_ref[base_cols + ["csv"]]
    ref_df.columns = ["anio", "mod", "url"]
    for i, row in ref_df.iterrows():
        download_zip_unzip(row["url"], row["anio"], row["mod"])


