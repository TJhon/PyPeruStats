import pandas as pd

def enaho_table(table_soup):
    rows = table_soup.find_all("tr")

    data = []

    for row in rows[1:]:
        cols = row.find_all("td")
        if not cols:
            continue

        # csv es opcional (no siempre existe)
        csv = None
        try:
            if len(cols) > 10 and cols[10].find("a"):
                csv = cols[10].find("a")["href"]
        except Exception:
            pass

        data.append({
            "nro": cols[0].get_text(strip=True),
            "anio": int(cols[1].get_text(strip=True)),
            "periodo": cols[2].get_text(strip=True),
            "cod_encuesta": cols[3].get_text(strip=True),
            "encuesta": cols[4].get_text(strip=True),
            "cod_modulo": int(cols[5].get_text(strip=True)),
            "modulo": cols[6].get_text(strip=True),
            "ficha": cols[7].find("a")["href"] if cols[7].find("a") else None,
            "spss": cols[8].find("a")["href"] if cols[8].find("a") else None,
            "stata": cols[9].find("a")["href"] if cols[9].find("a") else None,
            "csv": csv,
        })

    return pd.DataFrame(data)

import os, requests
import zipfile

def download_zip_unzip(
    zip_url, anio, mod_number: str, download_dir, 
    unzip_dir, 
    force=False, remove_zip=True
):
    dir = download_dir + f"/{anio}/"
    os.makedirs(dir, exist_ok=True)

    mod_number = str(mod_number).zfill(3)
    name =  f"{anio}_mod_{mod_number}"
    name_download = dir  + name
    name_move = f"{unzip_dir}/{anio}/{name}"

    if force or not os.path.exists(name + ".zip"):
        # print("Descargando")
        with open(name_download + ".zip", "wb") as zip_origin:
            zip_bin = requests.get(zip_url).content
            zip_origin.write(zip_bin)

        with zipfile.ZipFile(name_download + ".zip", "r") as zip_ref:
            zip_ref.extractall(name_move)
    if remove_zip:
        os.remove(name + ".zip")
        return {'remove_zip': True}
    return {'remove_zip': False}

TYPE_FILES_EXT = {"csv": ".csv", "spss": ".sav", "stata": ".dta", "pdf": ".pdf"}

def search_files_ext(master_dir, types=["csv", "stata", "spss"], names_modules=None):
    file_data = []
    for root, _, filenames in os.walk(master_dir):
        for file in filenames:
            # Verificar si el archivo coincide con alguna de las extensiones especificadas
            if  not (
                any(file.endswith(TYPE_FILES_EXT[file_type]) for file_type in types)
                and "tabla" not in file.lower()
            ):
                continue
        
            file_path = os.path.join(root, file)  # Ruta absoluta
            file_size = os.path.getsize(file_path) / (
                1024 * 1024
            )  # Convertir tamaño a MB
            relative_path = os.path.relpath(root, master_dir)
            # print(relative_path)
            first_subdirectory = relative_path.split(os.sep)[1]
            # print(first_subdirectory)
            anio, _, mod = first_subdirectory.split("_")
            last_directory = os.path.basename(root)  # Última subcarpeta

            # Agregar datos a la lista
            file_data.append(
                {
                    "ultima_subcarpeta": last_directory,
                    "anio": anio,
                    "cod_modulo": mod,
                    "nombre_archivo": file,
                    "peso_mb": round(file_size, 2),
                    "ruta_absoluta": file_path,
                }
            )
    df  = pd.DataFrame(file_data)
    if names_modules is not None:
        ref = names_modules[['cod_modulo', 'modulo']]
        ref['cod_modulo'] = ref['cod_modulo'].astype(str).str.zfill(3)
        df = df.merge(ref)
    return df

# a = search_files_ext(r'E:\All\github jhon\PyPeruStats\dir\enaho\1_refzip')
# print(a)

def reorder_documentation(master_dir, path, method, ext=["pdf"]):
    pdf_docs = search_files_ext(master_dir, ext)
    pdf_docs["nombre_archivo"] = pdf_docs["nombre_archivo"].str.lower()
    index_docs = pdf_docs[["nombre_archivo", "peso_mb"]].drop_duplicates().index

    unique_docs = pdf_docs.iloc[index_docs]

    dir_output = f"{path}/documentation_pdf"
    os.makedirs(dir_output, exist_ok=True)
    for _, row in unique_docs.iterrows():
        output_filename = f"{row['anio']}_{row['cod_modulo']}_{row['nombre_archivo']}"
        output_filename = os.path.join(
            dir_output, output_filename.replace(" ", "_")
        )
        method(row["ruta_absoluta"], output_filename)
    print(f"Documentacion en : {dir_output}")
