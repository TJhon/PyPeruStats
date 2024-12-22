import os, requests, zipfile
import pandas as pd
from unidecode import unidecode

TYPE_FILES_EXT = {
    "csv": ".csv",
    'spss': ".sav",
    'pdf': '.pdf'
}

TRASH = "./trash/"

def clean_names(df: pd.DataFrame):
    df.columns = [unidecode(c).lower().replace(" ", "_").replace(".", "_").strip() for c in df.columns]
    df.rename(columns={'ano': 'anio', 'a_no': 'anio'}, inplace=True)


def get_extract_zip(zip_url, anio, mod_number:str, TRASH):
    TRASH_ = TRASH + f"/{anio}/"
    os.makedirs(TRASH_, exist_ok=True)
    mod_number = str(mod_number).zfill(2)

    name = TRASH_ + f"{anio}_{mod_number}"
    with open(name + '.zip', 'wb') as zip_origin:
        zip_bin = requests.get(zip_url).content
        zip_origin.write(zip_bin)
    with zipfile.ZipFile(name + ".zip", 'r') as zip_ref:
        zip_ref.extractall(name)
    os.remove(name + '.zip')

def get_all_data_year(year, data, break_year = 2006):
    df = data.copy()
    df_ref = df.query("anio == @year")
    is_spsss = year < break_year
    base_cols = ['anio', 'codigo_modulo']
    if is_spsss:
        ref_df = df_ref[base_cols + ["spss"]]
    else:
        ref_df = df_ref[base_cols + ["csv"]]
    ref_df.columns = ['anio', 'mod', 'url']
    for i, row in ref_df.iterrows():
        get_extract_zip(row['url'], row['anio'], row['mod'])

def search_files_ext(type = 'spss', dir_master_trash = TRASH):
    file_data = []
    for root, _, filenames in os.walk(dir_master_trash):

        for file in filenames:
            if file.endswith(TYPE_FILES_EXT[type]) and "tabla" not in file.lower():  # Filtrar archivos .dta y excluir "tabla"
                file_path = os.path.join(root, file)  # Ruta absoluta
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convertir tamaño a MB
                relative_path = os.path.relpath(root, dir_master_trash)
                first_subdirectory = relative_path.split(os.sep)[0]
                anio, mod = first_subdirectory.split('_')
                last_directory = os.path.basename(root)  # Última subcarpeta

                # Agregar datos a la lista
                file_data.append({
                    "ultima_subcarpeta": last_directory,
                    "anio": anio,
                    "mod": mod,
                    "nombre_archivo": file,
                    "peso_mb": round(file_size, 2),
                    "ruta_absoluta": file_path
                })
    return file_data