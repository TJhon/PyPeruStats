import os
import sqlite3
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pandas as pd
import requests


class BCRPDataProcessor:
    """
    A data processing utility for retrieving and managing statistical series from the
    Peruvian Central Reserve Bank (BCRP) API.

    This class provides functionality to:
    - Fetch time series data across different frequencies (daily, monthly, quarterly, annual)
    - Cache and process API responses
    - Convert JSON data to pandas DataFrames
    - Optional parallel processing of multiple series
    - SQLite database caching

    Args:
        codes (list): List of statistical series codes to retrieve
        start_date (str): Start date for data retrieval in 'YYYY-MM-DD' format
        end_date (str): End date for data retrieval in 'YYYY-MM-DD' format
        format_date (str, optional): Date format for parsing. Defaults to '%Y-%m-%d'
        url (str, optional): Base URL for BCRP API. Defaults to BCRP statistics API endpoint
        parallel (bool, optional): Enable parallel processing of series. Defaults to False
        cache_dir (str, optional): Directory for storing cache files. Defaults to 'cache'
        db_name (str, optional): SQLite database filename. Defaults to 'cache.sqlite'

    Example:
        processor = DataProcessor(
            codes=['PBI_1D', 'IPC_2M'],
            start_date='2020-01-01',
            end_date='2023-12-31',
            parallel=True
        )
        results = processor.process_data()
    """

    def __init__(
        self,
        codes,
        start_date,
        end_date,
        format_date="%Y-%m-%d",
        url="https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codes}/json/{begin}/{end}/ing",
        parallel=False,
        cache_dir="cache",
        db_name="cache.sqlite",
    ):
        """Initialize the DataProcessor with configuration for API data retrieval."""
        self.codes = codes
        self.start_date = start_date
        self.end_date = end_date
        self.url = url
        self.format_date = format_date
        self.parallel = parallel
        self.cache_dir = cache_dir
        self.db_path = os.path.join(cache_dir, db_name)
        self.ref_date_formats = {"A": "%Y", "Q": "Q", "M": "%b.%Y", "D": "%d.%b.%y"}

    @staticmethod
    def separar_por_indice(codigos):
        """
        Classify codes by their last character (frequency indicator).

        Args:
            codigos (list): List of statistical series codes

        Returns:
            dict: Dictionary with frequency indicators as keys and corresponding codes as values.
                  Valid frequency indicators: 'D' (daily), 'M' (monthly),
                  'Q' (quarterly), 'A' (annual)

        Example:
            codes = ['PBI_1D', 'IPC_2M', 'EXPORT_1A']
            result = DataProcessor.separar_por_indice(codes)
            # Returns: {'D': ['PBI_1D'], 'M': ['IPC_2M'], 'A': ['EXPORT_1A']}
        """
        diccionario = defaultdict(list)
        indices_validos = {"D", "M", "Q", "A"}
        for codigo in codigos:
            last_char = codigo[-1]
            if last_char in indices_validos:
                diccionario[last_char].append(codigo)
        return dict(diccionario)

    def date_formats(self, date_str):
        """
        Convert a date string to different formats based on frequency.

        Args:
            date_str (str): Date string to convert, matching self.format_date

        Returns:
            dict: A dictionary with date formats for different frequencies:
                - 'D': Full date (YYYY-MM-DD)
                - 'M': Year-month format (YYYY-MM)
                - 'Q': Year and quarter (YYYY-Q)
                - 'A': Year (YYYY)

        Example:
            processor = DataProcessor(...)
            formats = processor.date_formats('2023-06-15')
            # Returns: {'D': '2023-06-15', 'M': '2023-06', 'Q': '2023-2', 'A': '2023'}
        """
        date_obj = datetime.strptime(date_str, self.format_date)
        return {
            "D": date_obj.strftime("%Y-%m-%d"),
            "M": date_obj.strftime("%Y-%m"),
            "Q": f"{date_obj.year}-{(date_obj.month - 1) // 3 + 1}",
            "A": date_obj.strftime("%Y"),
        }

    def get_data_api(self, codes, freq, str_date, end_date):
        """
        Retrieve data from BCRP API for specified series codes and date range.

        Args:
            codes (list): List of statistical series codes
            freq (str): Frequency indicator ('D', 'M', 'Q', 'A')
            str_date (str): Start date for data retrieval
            end_date (str): End date for data retrieval

        Returns:
            dict: JSON response from the BCRP API containing time series data

        Raises:
            requests.RequestException: If there's an error retrieving data from the API
        """
        codes = [cd.strip() for cd in codes]
        codes_j = "-".join(codes)
        str_date_f = self.date_formats(str_date)
        end_date_f = self.date_formats(end_date)
        root_url = self.url.format(
            codes=codes_j, begin=str_date_f[freq], end=end_date_f[freq]
        )
        # print(root_url)
        response = requests.get(root_url).json()
        return response

    @staticmethod
    def json_to_df(json):
        """
        Convert BCRP API JSON response to a pandas DataFrame.

        Args:
            json (dict): JSON response from BCRP API

        Returns:
            pandas.DataFrame: DataFrame with time series data,
            columns include 'fecha' and series names with numeric values

        Note:
            - Converts Spanish month abbreviations to English
            - Converts series values to numeric, handling errors gracefully
        """
        series_names = [serie["name"] for serie in json["config"]["series"]]
        periods = json["periods"]
        df = pd.DataFrame(
            [
                {"fecha": period["name"], **dict(zip(series_names, period["values"]))}
                for period in periods
            ]
        )
        meses = {"Ene": "Jan", "Abr": "Apr", "Ago": "Aug", "Set": "Sep", "Dic": "Dec"}
        for mes_es, mes_en in meses.items():
            df["fecha"] = df["fecha"].str.replace(mes_es, mes_en)
        for serie in series_names:
            df[serie] = pd.to_numeric(df[serie], errors="coerce")
        return df

    def df_date_format(self, df, date_method="A", quarter_to_timestamp=True):
        """
        Apply appropriate date formatting to DataFrame based on frequency.

        Args:
            df (pandas.DataFrame): Input DataFrame with 'fecha' column
            date_method (str, optional): Frequency method. Defaults to 'A' (annual)
            quarter_to_timestamp (bool, optional): Convert quarters to end-of-quarter timestamp.
                                                   Defaults to True

        Returns:
            pandas.DataFrame: DataFrame with parsed datetime index

        Note:
            - Handles different date formatting for various frequencies
            - Optionally converts quarterly periods to end-of-quarter timestamps
        """
        if date_method == "Q":
            df["fecha"] = pd.PeriodIndex(
                df["fecha"].str.replace(r"Q(\d)\.(\d{2})", r"\2Q\1", regex=True),
                freq="Q",
            )
            if quarter_to_timestamp:
                df["fecha"] = df["fecha"].dt.to_timestamp(how="end")
            return df
        df["fecha"] = pd.to_datetime(
            df["fecha"], format=self.ref_date_formats[date_method]
        )
        return df

    def save_to_sqlite(self, data_frame):
        """
        Save processed DataFrames to a SQLite database.

        Args:
            data_frame (dict): Dictionary of DataFrames with frequency as keys

        Note:
            - Creates cache directory if it doesn't exist
            - Saves each DataFrame as a separate table in the SQLite database
            - Tables are named with 'freq_' prefix followed by frequency indicator
        """
        os.makedirs(self.cache_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        for freq, df in data_frame.items():
            table_name = f"freq_{freq}"
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()

    def process_data(self, save_sqlite=False):
        """
        Process data from the BCRP (Central Reserve Bank of Peru) API for multiple series codes.

        This method retrieves statistical data from the BCRP API for different time series codes,
        handling multiple frequencies (daily, monthly, quarterly, annual) and performing
        data transformations.

        Args:
            save_sqlite (bool, optional): If True, saves the processed data to a SQLite database.
                Defaults to False.

        Returns:
            dict: A dictionary containing DataFrames for each frequency, with keys representing
            the frequency type ('D' for daily, 'M' for monthly, 'Q' for quarterly, 'A' for annual).
            Each DataFrame includes processed time series data with formatted dates and numeric values.

        Note:
            - Supports optional parallel processing of series
            - Can optionally save data to SQLite for caching and further analysis

        Example:
            processor = DataProcessor(
                codes=['PBI_1D', 'IPC_2M'],
                start_date='2020-01-01',
                end_date='2023-12-31'
            )
            results = processor.process_data(save_sqlite=True)
        """
        resultado = self.separar_por_indice(self.codes)
        data_result = {}

        def process_freq(freq):
            a = self.get_data_api(
                resultado[freq],
                freq=freq,
                str_date=self.start_date,
                end_date=self.end_date,
            )
            b = self.json_to_df(a)
            c = self.df_date_format(b, freq)
            data_result[freq] = c

        if self.parallel:
            with ThreadPoolExecutor() as executor:
                executor.map(process_freq, resultado.keys())
        else:
            for freq in resultado.keys():
                process_freq(freq)

        if save_sqlite:
            self.save_to_sqlite(data_result)

        return data_result
