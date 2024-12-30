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


def get_extract_zip(
    zip_url, anio, mod_number: str, master_dir, force=False, remove_zip=True
):
    dir = master_dir + f"/{anio}/"
    os.makedirs(dir, exist_ok=True)
    mod_number = str(mod_number).zfill(2)

    name = dir + f"{anio}_{mod_number}"

    if force or not os.path.exists(name + ".zip"):
        # print()
        with open(name + ".zip", "wb") as zip_origin:
            zip_bin = requests.get(zip_url).content
            zip_origin.write(zip_bin)
        with zipfile.ZipFile(name + ".zip", "r") as zip_ref:
            zip_ref.extractall(name)
    if remove_zip:
        os.remove(name + ".zip")


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
        get_extract_zip(row["url"], row["anio"], row["mod"])


def search_files_ext(master_dir, types=["csv", "stata", "spss"]):
    file_data = []
    for root, _, filenames in os.walk(master_dir):
        for file in filenames:
            # Verificar si el archivo coincide con alguna de las extensiones especificadas
            if (
                any(file.endswith(TYPE_FILES_EXT[file_type]) for file_type in types)
                and "tabla" not in file.lower()
            ):
                file_path = os.path.join(root, file)  # Ruta absoluta
                file_size = os.path.getsize(file_path) / (
                    1024 * 1024
                )  # Convertir tamaño a MB
                relative_path = os.path.relpath(root, master_dir)
                first_subdirectory = relative_path.split(os.sep)[1]
                anio, mod = first_subdirectory.split("_")
                last_directory = os.path.basename(root)  # Última subcarpeta

                # Agregar datos a la lista
                file_data.append(
                    {
                        "ultima_subcarpeta": last_directory,
                        "anio": anio,
                        "mod": mod,
                        "nombre_archivo": file,
                        "peso_mb": round(file_size, 2),
                        "ruta_absoluta": file_path,
                    }
                )
    return pd.DataFrame(file_data)
