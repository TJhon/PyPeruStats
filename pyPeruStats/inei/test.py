import os
import shutil
import zipfile
import pandas as pd
from pathlib import Path
from typing import List, Literal, Optional
from tqdm import tqdm
from joblib import Parallel, delayed
from bs4 import BeautifulSoup

# === FUNCIONES AUXILIARES (tus funciones mejoradas) ===

def html_to_dataframe(html: str) -> pd.DataFrame:
    """Convierte el HTML de respuesta del INEI en DataFrame con spss/stata/csv/dbf detectados dinámicamente."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        return pd.DataFrame()

    rows = table.find_all("tr")
    if len(rows) <= 1:
        return pd.DataFrame()

    data = []
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue

        nro = cols[0].get_text(strip=True)
        try:
            anio = int(cols[1].get_text(strip=True))
        except:
            anio = None
        periodo = cols[2].get_text(strip=True)
        cod_encuesta = cols[3].get_text(strip=True)
        encuesta = cols[4].get_text(strip=True)
        try:
            cod_modulo = int(cols[5].get_text(strip=True))
        except:
            cod_modulo = None
        modulo = cols[6].get_text(strip=True)
        ficha = cols[7].find("a")["href"] if cols[7].find("a") else None

        # Detectar formatos
        formatos = {"spss": None, "stata": None, "csv": None, "dbf": None}
        for cell in cols[8:]:
            a = cell.find("a")
            if not a or not a.get("href"):
                continue
            href = a["href"]
            title = (a.get("title") or "").lower()
            if "spss" in title or "/SPSS/" in href:
                formatos["spss"] = href
            elif "stata" in title or "/STATA/" in href:
                formatos["stata"] = href
            elif "csv" in title or "/CSV/" in href:
                formatos["csv"] = href
            elif "dbf" in title or "/DBF/" in href:
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
            **formatos
        })
    return pd.DataFrame(data)


# === CONFIGURACIÓN GLOBAL ===
ENCUESTAS_CONFIG = {
    "enaho": {"nombre_form": "Condiciones%20de%20Vida%20y%20Pobreza%20-%20ENAHO", "trimestre": "55"},
    "endes": {"nombre_form": "Encuesta%20Demogr%E1fica%20y%20de%20Salud%20Familiar%20-%20ENDES", "trimestre": "5"},
    "enapres": {"nombre_form": "Encuesta%20Nacional%20de%20Programas%20Presupuestales%20-%20ENAPRES", "trimestre": "18"}
}

SESSION_COOKIE = "ASPSESSIONIDSSXCRQBD=XXXXXX"  # Actualízalo si es necesario
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0"
BASE_URL = "https://proyectos.inei.gob.pe/iinei/srienaho"


import subprocess

def ejecutar_curl_encuesta(encuesta: str, anno: int, trimestre: str = None):
    if encuesta not in ENCUESTAS_CONFIG:
        raise ValueError(f"Encuesta no soportada: {encuesta}")
    config = ENCUESTAS_CONFIG[encuesta]
    trimestre = trimestre or config["trimestre"]
    nombre_form = config["nombre_form"]
    data_raw = f"bandera=1&_cmbEncuesta={nombre_form}&_cmbAnno={anno}&_cmbTrimestre={trimestre}"

    cmd = [
        "curl", "-s",
        f"{BASE_URL}/cambiaPeriodo.asp",
        "-H", "Accept: */*",
        "-H", "Accept-Language: es,en;q=0.9",
        "-H", "Connection: keep-alive",
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-b", SESSION_COOKIE,
        "-H", f"Origin: {BASE_URL}",
        "-H", f"Referer: {BASE_URL}/Consulta_por_Encuesta.asp",
        "-H", "Sec-Fetch-Dest: empty",
        "-H", "Sec-Fetch-Mode: cors",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", f"User-Agent: {USER_AGENT}",
        "-H", 'sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Opera";v="124"',
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "--data-raw", data_raw
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def normalize_modulo_name(name: str) -> str:
    """Elimina contenido entre paréntesis y normaliza espacios."""
    import re
    name = re.sub(r"\s*\(.*?\)\s*", " ", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name.replace("/", "_").replace("\\", "_")


# === CLASE PRINCIPAL ===
class MicrodatosINEIFetcher:
    def __init__(
        self,
        encuesta: Literal["enaho", "endes", "enapres"],
        years: List[int],
        dir_master: str = "./microdatos_inei",
        n_jobs: int = 2
    ):
        self.encuesta = encuesta
        self.years = years
        self.dir_master = Path(dir_master) / encuesta
        self.n_jobs = n_jobs
        self.df_modules = pd.DataFrame()
        self.zips_dir = self.dir_master / "0_zips"
        self.unzipped_dir = self.dir_master / "1_unzipped"
        self.ordered_dir = self.dir_master / "2_ordenado"

    def fetch_modules(self):
        """Obtiene módulos para todos los años usando curl + parsing."""
        def _fetch_year(anno):
            html = ejecutar_curl_encuesta(self.encuesta, anno)
            return html_to_dataframe(html)

        results = Parallel(n_jobs=self.n_jobs)(
            delayed(_fetch_year)(y) for y in tqdm(self.years, desc=f"Descargando {self.encuesta}")
        )
        self.df_modules = pd.concat(results, ignore_index=True).drop_duplicates()
        return self

    def download_zips(
        self,
        formats: List[str] = ["stata", "spss", "csv", "dbf"],
        force: bool = False,
        modules: List[int] = [],
        remove_zip: bool = False
    ):
        os.makedirs(self.zips_dir, exist_ok=True)
        os.makedirs(self.unzipped_dir, exist_ok=True)

        modules = [str(x).zfill(3) for x in modules]
        df = self.df_modules.copy()
        df["cod_modulo"] = df["cod_modulo"].astype(str).str.zfill(3)
        df = df.query('cod_modulo in @modules')



        for _, row in tqdm(df.iterrows(), total=len(df), desc="Descargando .zip"):
            # Elegir primer formato disponible
            url = None
            for fmt in formats:
                if pd.notna(row[fmt]):
                    url = f"{BASE_URL}/{row[fmt]}"
                    break
            if not url:
                continue

            anio = str(row["anio"])
            mod = row["cod_modulo"]
            zip_path = self.zips_dir / f"{anio}_mod_{mod}.zip"
            extract_to = self.unzipped_dir / f"{anio}_mod_{mod}"

            if force or not zip_path.exists():
                import requests
                resp = requests.get(url)
                resp.raise_for_status()
                with open(zip_path, "wb") as f:
                    f.write(resp.content)

            if not extract_to.exists():
                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(extract_to)

            if remove_zip:
                zip_path.unlink(missing_ok=True)
        return self

    def organize_files(
        self,
        order_by: Literal["modulo", "anio"] = "modulo",
        keep_original_names: bool = True,
        move_or_copy: Literal["move", "copy"] = "copy",
        ext_documentation: List[str] = ["pdf"]
    ):
        os.makedirs(self.ordered_dir, exist_ok=True)
        move_fn = shutil.move if move_or_copy == "move" else shutil.copy2

        # Recopilar archivos relevantes
        relevant_exts = {".csv", ".sav", ".dta", ".dbf"}
        data = []

        for root, _, files in os.walk(self.unzipped_dir):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in relevant_exts:
                    continue
                full_path = Path(root) / file
                rel_parts = Path(root).relative_to(self.unzipped_dir).parts
                if not rel_parts:
                    continue
                anio_mod = rel_parts[0]  # ej: "2014_mod_001"
                parts = anio_mod.split("_mod_")
                if len(parts) != 2:
                    continue
                anio, cod_modulo = parts[0], parts[1]

                # Encontrar nombre de módulo desde df
                mod_row = self.df_modules[
                    (self.df_modules["anio"] == int(anio)) &
                    (self.df_modules["cod_modulo"].astype(str).str.zfill(3) == cod_modulo)
                ]
                modulo_name = mod_row["modulo"].iloc[0] if not mod_row.empty else "Desconocido"
                norm_name = normalize_modulo_name(modulo_name)

                if order_by == "modulo":
                    folder = self.ordered_dir / "por_modulo" / f"{cod_modulo}_{norm_name}"
                    out_name = f"{anio}{ext}"
                else:
                    folder = self.ordered_dir / "por_anio" / anio
                    out_name = f"{cod_modulo}_{norm_name}{ext}"

                os.makedirs(folder, exist_ok=True)
                dest = folder / out_name
                move_fn(full_path, dest)
                data.append({"anio": anio, "cod_modulo": cod_modulo, "file": dest})

        # === Documentación (PDFs) ===
        pdf_dir = self.ordered_dir / "documentacion"
        os.makedirs(pdf_dir, exist_ok=True)
        seen = set()

        for root, _, files in os.walk(self.unzipped_dir):
            for file in files:
                if not file.lower().endswith(".pdf"):
                    continue
                src = Path(root) / file
                size = src.stat().st_size
                key = (file.lower(), size)
                if key in seen:
                    continue
                seen.add(key)
                dest = pdf_dir / f"{src.parent.name}_{file}"
                move_fn(src, dest)

        print(f"✅ Archivos organizados en: {self.ordered_dir}")
        return self
    

if __name__ == "__main__":
    # Ejemplo: ENDES 2011-2013
    # fetcher = MicrodatosINEIFetcher(
    #     encuesta="endes",
    #     years=[2011, 2013],
    #     dir_master="./datos_inei",
    #     n_jobs=2
    # )
    # fetcher.fetch_modules().download_zips(formats=["stata", "dbf"]).organize_files(
    #     order_by="anio",
    #     keep_original_names=True,
    #     move_or_copy="copy"
    # )
    # Ejemplo: ENAHO 2011-2013
    fetcher = MicrodatosINEIFetcher(
        encuesta="enaho",
        years=[2011, 2013],
        dir_master="./datos_inei",
        n_jobs=2
    )
    fetcher.fetch_modules().download_zips(formats=["stata", "csv"], modules=list(range(0, 5))).organize_files(
        order_by="anio",
        keep_original_names=True,
        move_or_copy="copy"
    )
 