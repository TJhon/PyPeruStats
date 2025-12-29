import pandas as pd
import requests
from bs4 import BeautifulSoup
import re, math
from io import StringIO
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

URL_HOMOLOGACION = "https://she.mtc.gob.pe/ieqhomgestionar/index"

new_names = [
    "n",
    "type",
    "cert",
    "brand",
    "model",
    "manufacturer",
    "function",
    "date",
    "nan",
]


class TelMTC:
    def __init__(self, marca="", num_cert="", model="", empresa=""):
        self.params = {
            "NumeroCertificado": num_cert,
            "Marca": marca,
            "Modelo": model,
            "Empresa": empresa,
        }
        self.first_page()

    def post_data(self):
        response = requests.post(URL_HOMOLOGACION, data=self.params)
        return response

    def first_page(self, total_n_by_page=10):
        response = self.post_data()
        self.first_page_response = response
        soup = self.to_soup(response.content)
        total_registros = soup.find("span", class_="total-registros").get_text()
        resultado = re.search(r"\d+", total_registros)
        numero = int(resultado.group())
        total_pages = math.ceil(numero / total_n_by_page)
        self.total_pages = total_pages

    def update_params(self, n_page):
        self.params["hdPag"] = n_page
        response_n = self.post_data()
        return response_n

    @staticmethod
    def to_soup(content_html):
        soup = BeautifulSoup(content_html, features="html.parser")
        return soup

    @staticmethod
    def html_to_pandas(html) -> pd.DataFrame:
        table_data = html.find("table", class_="table")
        data = pd.read_html(StringIO(str(table_data)))[0]
        return data

    def fetch_data(self):
        content_html = self.first_page_response.content
        total_pages = self.total_pages
        html = self.to_soup(content_html)
        data_fp = self.html_to_pandas(html)
        data = [data_fp]

        # Procesar las páginas restantes en paralelo
        def fetch_page_data(page):
            response_n = self.update_params(page)
            html_n = self.to_soup(response_n.content)
            return self.html_to_pandas(html_n)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(fetch_page_data, page): page
                for page in range(2, total_pages + 1)
            }
            for future in tqdm(as_completed(futures), total=len(futures)):
                try:
                    data.append(future.result())
                except Exception as e:
                    print(f"Error procesando página: {futures[future]} - {e}")

        # Combinar todos los datos en un DataFrame final
        data_final = pd.concat(data, ignore_index=True)
        data_final.columns = new_names
        data_final["date"] = pd.to_datetime(data_final["date"], format="%d/%m/%Y")
        data_final.drop(columns=["n", "nan"], inplace=True)
        data_final = data_final.sort_values("date", ascending=False)

        return data_final
