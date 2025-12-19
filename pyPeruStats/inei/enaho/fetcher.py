# enaho metodologia actualizada

import requests, shutil
import pandas as pd
from bs4 import BeautifulSoup
from utils import enaho_table, download_zip_unzip, search_files_ext, reorder_documentation


from datetime import datetime
from joblib import Parallel, delayed
from tqdm import tqdm
import os

BASE = "https://proyectos.inei.gob.pe/iinei/srienaho"



import os, requests
import zipfile, subprocess

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



TYPE_FILES_EXT = {"csv": ".csv", "spss": ".sav", "stata": ".dta", "pdf": ".pdf", 'dbf':'.dbf'}

def search_files_ext(master_dir, types=["csv", "stata", "spss", 'dbf'], names_modules=None):
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


class EnahoFetcher:
    def __init__(self, years:list, workers=2):
        self.years = years
        self.workers = workers
    def fetch_modules(self):
        results = Parallel(n_jobs=self.workers)(
            delayed(obtener_modulos_enaho)(x)
            for x in tqdm(self.years, desc="Consultando módulos")
        )

        df_modulos = pd.concat(results, ignore_index=True)
        # print(df_modulos)
        self.df = df_modulos
        self._get_modules_bycodesnames()
        self._get_modules_byname()

        return self
    
    def _get_modules_bycodesnames(self):
        """
        Muestra los modulos que estan disponibles para un grupo de anios
        """
        modules = (
            self.df.groupby(["cod_modulo", "modulo"])["anio"]
            .apply(lambda x: " ".join(map(str, sorted(x.unique(), reverse=True))))
            .reset_index()
        )
        self.modules = modules
    def _get_modules_byname(self):
        """
        Muestra los modulos que estan disponibles para un grupo de anios
        """
        modules = (
            self.df.groupby(["modulo"])["anio"]
            .apply(lambda x: " ".join(map(str, sorted(x.unique(), reverse=True))))
            .reset_index()
        )
        self.modules_names = modules

    
class EnahoDownload:
    def __init__(
            self, fetcher:EnahoFetcher, modules = [], 
            formats:list=['stata', 'csv', 'spss', 'dbf'],  directory='./dir/enaho',
            delete_zip = False, force_redownload = False
            ):
        # directories
        self.master_dir=directory
        self.formats = formats
        self.modules=modules
        self.zips = f'{directory}/0_zips'
        self.deleted = False
        self.force = force_redownload
        self.delete_zip = delete_zip
        
        self.refzip = f'{directory}/1_refzip'
        self.orderzip = f'{directory}/2_ordenado'
        for dd in [self.zips, self.refzip, self.orderzip]: os.makedirs(dd, exist_ok=True)
        self.df_modules=fetcher.df
        print(fetcher.df.columns)

    def filter_by_codmod(self):
        df = self.df_modules.query('cod_modulo in @self.modules')
        df= df[['anio', 'cod_modulo'] + self.formats]
        self.df_download:pd.DataFrame = df
        return self
    
    def download(self):
        # todo: tomando los workers del fetcher se necesita procesar de manera parallela
        if len(self.modules)>0:
            self.filter_by_codmod()
        formats=self.formats


        for i, row in tqdm(self.df_download.iterrows(), total = self.df_download.shape[0]):
            url = BASE + "/" + row[formats[0]] if row[formats[0]] else row[formats[1]]
            anio = str(row['anio'])
            mod_number = str(row['cod_modulo'])
            download_dir = self.zips
            unzip_dir = self.refzip
            results = download_zip_unzip(
                url, anio, mod_number, download_dir, unzip_dir, force = self.force, remove_zip=self.delete_zip
            )
            if i == 1 and results.get('remove_zip', False):
                self.deleted = results.get('remove_zip', True)
        return self
    def organize_files(self, order_by='modules', order_documentation = True, ext_documentation= ['pdf'], move_or_copy = 'copy', keep_names = True):
        
        dir_output = self.orderzip

        df_files = search_files_ext(self.refzip, names_modules=self.df_modules)
        df_files["version"] = df_files.groupby(["anio", "cod_modulo"]).cumcount() + 1

        if move_or_copy == 'copy':
            mv_cb = shutil.copy2
        else:
            mv_cb = shutil.move
        print(df_files)
        data = []

        for _, row in df_files.iterrows():
            _, file_ext = os.path.splitext(row["nombre_archivo"])

            if row["version"] > 1:
                file_ext = f"_{row['version']}{file_ext}"
            cod_modulo = row['cod_modulo'].zfill(3)
            # todo: para row['modulo'] se debe optar por eliminar lo que esta dentro del parentesis incluyendo el parentesis
            name_dir_modulo = f'{cod_modulo}_{row['modulo']}' if keep_names else cod_modulo
            if order_by.startswith('mod'):
                folder_path = os.path.join(dir_output, order_by, name_dir_modulo)
                output_file_name = f"{row['anio']}{file_ext}"
            else:  # "year_first"
                folder_path = os.path.join(dir_output, order_by, str(row["anio"]))
                output_file_name = f"{name_dir_modulo}{file_ext}"

            os.makedirs(folder_path, exist_ok=True)

            destination_path = os.path.join(folder_path, output_file_name)

            mv_cb(row["ruta_absoluta"], destination_path)
            data.append(
                {
                    "anio": row["anio"],
                    "cod_modulo": row["cod_modulo"],
                    "nombre_archivo": output_file_name,
                    "peso_mb": row["peso_mb"],
                    "ruta_absoluta": row["ruta_absoluta"],
                }
            )
        if order_documentation:
            reorder_documentation(self.refzip, self.orderzip, mv_cb, ext=ext_documentation)

        # return pd.DataFrame(data)
        return self


    



# Diccionario de configuración global para cada encuesta
ENCUESTAS_CONFIG = {
    "enaho": {
        "nombre_form": "Condiciones%20de%20Vida%20y%20Pobreza%20-%20ENAHO",
        "trimestre_default": "55"
    },
    "endes": {
        "nombre_form": "Encuesta%20Demogr%E1fica%20y%20de%20Salud%20Familiar%20-%20ENDES",
        "trimestre_default": "5"
    },
    "enapres": {
        "nombre_form": "Encuesta%20Nacional%20de%20Programas%20Presupuestales%20-%20ENAPRES",
        "trimestre_default": "18"
    }
}

# Cookie base (puedes actualizarla si cambia)
SESSION_COOKIE = "ASPSESSIONIDSSXCRQBD=XXXXXX"  # <-- Reemplazar con valor válido si es necesario

# User-Agent moderno (lo mantienes fijo según tu ejemplo)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0"

def ejecutar_curl_encuesta(encuesta: str, anno: int, trimestre: str = None):
    """
    Ejecuta un curl para cambiar el periodo de una encuesta específica.

    Parámetros:
    - encuesta (str): "enaho", "endes" o "enapres"
    - anno (int): año de la encuesta (ej. 2021)
    - trimestre (str, opcional): trimestre; si no se da, se usa el default del tipo de encuesta
    """
    if encuesta not in ENCUESTAS_CONFIG:
        raise ValueError(f"Encuesta '{encuesta}' no soportada. Opciones: {list(ENCUESTAS_CONFIG.keys())}")

    config = ENCUESTAS_CONFIG[encuesta]
    trimestre_usar = trimestre if trimestre is not None else config["trimestre_default"]
    nombre_form = config["nombre_form"]

    # Construir datos del POST
    data_raw = f"bandera=1&_cmbEncuesta={nombre_form}&_cmbAnno={anno}&_cmbTrimestre={trimestre_usar}"

    # Armar comando curl como lista de argumentos (más seguro que string)
    cmd = [
        "curl",
        "https://proyectos.inei.gob.pe/iinei/srienaho/cambiaPeriodo.asp",
        "-H", "Accept: */*",
        "-H", "Accept-Language: es,en;q=0.9,en-US;q=0.8,ca;q=0.7,zh-CN;q=0.6,zh;q=0.5",
        "-H", "Connection: keep-alive",
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-b", SESSION_COOKIE,
        "-H", "Origin: https://proyectos.inei.gob.pe",
        "-H", "Referer: https://proyectos.inei.gob.pe/iinei/srienaho/Consulta_por_Encuesta.asp",
        "-H", "Sec-Fetch-Dest: empty",
        "-H", "Sec-Fetch-Mode: cors",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", f"User-Agent: {USER_AGENT}",
        "-H", 'sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Opera";v="124"',
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "--data-raw", data_raw
    ]

    print("Ejecutando curl para:", encuesta, anno, trimestre_usar)
    # Ejecutar el comando
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # print("✅ Respuesta recibida (primeros 500 chars):")
        # print(result.stdout[:3000])
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("❌ Error al ejecutar curl:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        raise


import pandas as pd
from bs4 import BeautifulSoup

def html_to_dataframe(html: str) -> pd.DataFrame:
    """
    Convierte el HTML de respuesta del INEI (tabla de microdatos) en un DataFrame robusto.
    Detecta dinámicamente los formatos disponibles: spss, stata, csv, dbf.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        return pd.DataFrame()  # No hay tabla

    rows = table.find_all("tr")
    if len(rows) <= 1:
        return pd.DataFrame()

    data = []

    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue  # fila incompleta

        # Extraer campos fijos
        nro = cols[0].get_text(strip=True)
        try:
            anio = int(cols[1].get_text(strip=True))
        except (ValueError, IndexError):
            anio = None
        periodo = cols[2].get_text(strip=True)
        cod_encuesta = cols[3].get_text(strip=True)
        encuesta = cols[4].get_text(strip=True)
        try:
            cod_modulo = int(cols[5].get_text(strip=True))
        except (ValueError, IndexError):
            cod_modulo = None
        modulo = cols[6].get_text(strip=True)
        ficha = cols[7].find("a")["href"] if cols[7].find("a") else None

        # Inicializar formatos
        formatos = {"spss": None, "stata": None, "csv": None, "dbf": None}

        # Las celdas de descarga empiezan desde la columna 8 en adelante
        download_cells = cols[8:]

        for cell in download_cells:
            a_tag = cell.find("a")
            if not a_tag or not a_tag.get("href"):
                continue

            href = a_tag["href"]
            title = a_tag.get("title", "").lower()

            if "spss" in title:
                formatos["spss"] = href
            elif "stata" in title:
                formatos["stata"] = href
            elif "csv" in title:
                formatos["csv"] = href
            elif "dbf" in title:
                formatos["dbf"] = href
            # Alternativa: si no hay title, usar la URL
            elif "/SPSS/" in href:
                formatos["spss"] = href
            elif "/STATA/" in href:
                formatos["stata"] = href
            elif "/CSV/" in href:
                formatos["csv"] = href
            elif "/DBF/" in href:
                formatos["dbf"] = href

        data.append({
            "nro": nro,
            "anio": anio,
            "periodo": periodo,
            "cod_encuesta": cod_encuesta,
            "encuesta": encuesta,
            "cod_modulo": cod_modulo,
            "modulo": modulo,
            "ficha": ficha,
            "spss": formatos["spss"],
            "stata": formatos["stata"],
            "csv": formatos["csv"],
            "dbf": formatos["dbf"],
        })

    return pd.DataFrame(data)


# Ejemplo de uso
if __name__ == "__main__":
    # Puedes probar con distintas combinaciones
    html = ejecutar_curl_encuesta("enaho", 2014)
    html_enaho = html_to_dataframe(html)
    print(html_enaho)
    html = ejecutar_curl_encuesta("endes", 2011)
    html_endes = html_to_dataframe(html)
    print(html_endes)
    html = ejecutar_curl_encuesta("enapres", 2010, trimestre="18")
    html_enapres = html_to_dataframe(html)
    print(html_enapres.columns)