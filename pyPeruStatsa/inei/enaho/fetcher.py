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


def obtener_modulos_enaho(anio: int = 2004) -> pd.DataFrame:
    """
    Obtiene los módulos disponibles de ENAHO para un año dado.
    
    Parámetros
    ----------
    anio : int, default 2004
        Año de la encuesta ENAHO
    
    Retorna
    -------
    pd.DataFrame
    """

    hoy = datetime.today()
    anio_actual = hoy.year

    # 1) No disponible antes de 2004
    if anio < 2004 or anio >= anio_actual:
        print(f"Los datos para el año {anio} no están disponibles.")
        return pd.DataFrame()



    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"{BASE}/Consulta_por_Encuesta.asp",
    }

    # 1) Cambiar encuesta
    session.post(
        f"{BASE}/CambiaEnc.asp",
        headers=headers,
        data={
            "bandera": "1",
            "_cmbEncuesta": "Condiciones de Vida y Pobreza - ENAHO",
            "_cmbEncuesta0": "2",
        },
    )

    # 2) Cambiar año
    session.post(
        f"{BASE}/CambiaAnio.asp",
        headers=headers,
        data={
            "bandera": "1",
            "_cmbEncuesta": "Condiciones de Vida y Pobreza - ENAHO",
            "_cmbAnno": str(anio),
            "_cmbEncuesta0": "2",
        },
    )

    # 3) Cambiar periodo (anual)
    resp_periodo = session.post(
        f"{BASE}/cambiaPeriodo.asp",
        headers=headers,
        data={
            "bandera": "1",
            "_cmbEncuesta": "Condiciones de Vida y Pobreza - ENAHO",
            "_cmbAnno": str(anio),
            "_cmbTrimestre": "55",
        },
    )

    soup = BeautifulSoup(resp_periodo.content, "html.parser")
    table = soup.find("table", {"border": "1"})

    if table is None:
        raise RuntimeError("No se encontró la tabla de resultados")

    return enaho_table(table)



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
            formats:list=['stata', 'csv'],  directory='./dir/enaho',
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
        # falta implementar descarga paralela usando los workers del fetcher
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


    



if __name__ == '__main__':
    import time

    enaho = EnahoFetcher([2004, 2024]).fetch_modules()
    print(enaho.modules)
    dwnl = EnahoDownload(enaho, [1, 2, 34]).download()
    dwnl.organize_files()
    