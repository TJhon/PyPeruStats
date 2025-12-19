from .utils import get_extract_zip, search_files_ext
import pandas as pd, time, os, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

MICRODATOS = "https://raw.githubusercontent.com/TJhon/PyPeruStats/refs/heads/inei/MetadataSources/INEI/microdatos_recolectados.csv"


class MICRODATOS_INEI:
    def __init__(
        self,
        survey="enaho",
        metadata_url=MICRODATOS,
        col_ref_encuesta="encuesta_ref",
    ):
        self.survey = survey
        self.metadata: pd.DataFrame = pd.read_csv(metadata_url)
        self.col_ref = col_ref_encuesta

        self._get_survey_data()
        self._get_modules()

    def _get_survey_data(self):
        metadata = self.metadata
        self.data_survey = metadata[metadata[self.col_ref] == self.survey]

    def _get_modules(self):
        modules = (
            self.data_survey.groupby(["codigo_modulo", "modulo"])["anio"]
            .apply(lambda x: " ".join(map(str, sorted(x.unique(), reverse=True))))
            .reset_index()
        )
        self.modules = modules

    def search(self, years=None, cod_modules=None, show_warnings=True):
        metadata = self.metadata.copy()
        filtered_data = metadata[
            metadata["anio"].isin(years) & metadata["codigo_modulo"].isin(cod_modules)
        ]
        missing_entries = {}
        if show_warnings:
            for module in cod_modules:
                module_years = filtered_data[filtered_data["codigo_modulo"] == module][
                    "anio"
                ].unique()
                missing_years = set(years) - set(module_years)

                if missing_years:
                    missing_entries[module] = list(missing_years)
                    print(
                        f"Advertencia: El código de módulo {module} no tiene registros para los años {missing_years}"
                    )

        self.filtered_data = filtered_data
        return self

    def download_default(
        self,
        format="csv",  # format: csv, spss, stata, pdf
        second_format="stata",
        force=False,
        master_dir=None,
        remove_zip=False,
        zip_dir="test_data",
        workers=1,
    ):
        start_time = time.time()
        if master_dir is None:
            master_dir = f"./{zip_dir}/inei_{self.survey}_download"
        self.master_dir = master_dir

        reference = self.filtered_data
        tasks = []
        results = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            with tqdm(total=len(reference), desc="Descargando") as pbar:
                for _, row in reference.iterrows():
                    col_href = format if pd.notna(row[format]) else second_format
                    _anio = row["anio"]
                    _mod = row["codigo_modulo"]
                    _url = row[col_href]

                    # Agregar tarea al ejecutor
                    tasks.append(
                        executor.submit(
                            get_extract_zip,
                            _url,
                            _anio,
                            _mod,
                            master_dir,
                            remove_zip=remove_zip,
                            force=force,
                        )
                    )

                for future in as_completed(tasks):
                    results.append(future.result())
                    pbar.update(1)
        elapsed_time = time.time() - start_time
        print(f"Descargas completadas en {elapsed_time:.2f} segundos.")

        self.relevant_files = search_files_ext(master_dir)
        return self

    def organize_files(
        self,
        dir_output=None,
        order_by="module",
        copy=True,
        order_documentation=True,
        ext_documentation=["pdf"],
        delete_master_dir=False,  # se tendra que descargar de nuevo todo
    ):  # year_first
        if dir_output is None:
            dir_output = "./data_inei/"
        df = self.relevant_files
        df["version"] = df.groupby(["anio", "mod"]).cumcount() + 1
        if copy:
            mv_cp = shutil.copy2
        else:
            mv_cp = shutil.move

        data = []

        for _, row in df.iterrows():
            _, file_ext = os.path.splitext(row["nombre_archivo"])

            if row["version"] > 1:
                file_ext = f"_{row['version']}{file_ext}"

            if order_by == "modules":
                folder_path = os.path.join(dir_output, order_by, row["mod"].zfill(3))
                output_file_name = f"{row['anio']}{file_ext}"
            elif order_by == "years":  # "year_first"
                folder_path = os.path.join(dir_output, order_by, str(row["anio"]))
                output_file_name = f"{row['mod']}{file_ext}"

            os.makedirs(folder_path, exist_ok=True)

            destination_path = os.path.join(folder_path, output_file_name)

            mv_cp(row["ruta_absoluta"], destination_path)
            data.append(
                {
                    "anio": row["anio"],
                    "mod": row["mod"],
                    "nombre_archivo": output_file_name,
                    "peso_mb": row["peso_mb"],
                    "ruta_absoluta": row["ruta_absoluta"],
                }
            )
        if order_documentation:
            self.reorder_documentation(self.master_dir, mv_cp, ext=ext_documentation)
        if delete_master_dir:
            shutil.rmtree(self.master_dir)
        return pd.DataFrame(data)

    @staticmethod
    def reorder_documentation(master_dir, method, ext=["pdf"]):
        pdf_docs = search_files_ext(master_dir, ext)
        pdf_docs["nombre_archivo"] = pdf_docs["nombre_archivo"].str.lower()
        index_docs = pdf_docs[["nombre_archivo", "peso_mb"]].drop_duplicates().index

        unique_docs = pdf_docs.iloc[index_docs]

        dir_output = "./data_inei/documentation_pdf"
        os.makedirs(dir_output, exist_ok=True)
        for _, row in unique_docs.iterrows():
            output_filename = f"{row['anio']}_{row['mod']}_{row['nombre_archivo']}"
            output_filename = os.path.join(
                dir_output, output_filename.replace(" ", "_")
            )
            method(row["ruta_absoluta"], output_filename)
        print(f"Documentacion en : {dir_output}")
