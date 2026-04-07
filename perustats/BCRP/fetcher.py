import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from perustats.BCRP.backup.utils import get_data_api, json_to_df
from perustats.BCRP.models import REF_DATE_FORMATS, SeriesRequest


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
        series: SeriesRequest,
        format_date="%Y-%m-%d",
    ):
        """Initialize the DataProcessor with configuration for API data retrieval."""
        self.series = series
        self.format_date = format_date

        self.ref_date_formats = REF_DATE_FORMATS

    def fetch_data(self):
        series = self.series
        freq_codes = series.freq_codes
        date_limits = series.date_limits

        for freq in freq_codes.keys():
            codes = freq_codes.get(freq)
            limits = date_limits.get(freq)
            start_date_freq = limits.get("start_date")
            end_date_freq = limits.get("end_date")
            data_json = get_data_api(codes, start_date_freq, end_date_freq)
            df_freq = json_to_df(data_json)

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


if __name__ == "__main__":
    a = BCRPDataProcessor(
        ["RD16085DA"],
        start_date="2002-01-02",
        end_date="2023-01-01",
    ).process_data()
    print(a)
