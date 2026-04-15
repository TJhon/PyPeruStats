import pandas as pd

from perustats.BCRP.cache import BCRPCache
from perustats.BCRP.metadata import BCRPMetadata
from perustats.BCRP.models import CACHE_DB, REF_DATE_FORMATS, BCRPSeries
from perustats.BCRP.utils import apply_date_format, get_data_api, json_to_df


class BCRPDataSeries:
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

    def __init__(self, series: BCRPSeries, format_date="%Y-%m-%d"):
        """Initialize the DataProcessor with configuration for API data retrieval."""
        self.series = series
        self.format_date = format_date
        self.ref_date_formats = REF_DATE_FORMATS

    def fetch_data(self, cache=None) -> "BCRPDataSeries":
        db_name = CACHE_DB if cache is None else cache
        metadata = BCRPMetadata(db_name)
        bcrp_cache = BCRPCache(db_name)
        series = self.series
        freq_codes = series.freq_codes
        date_limits = series.date_limits

        result = dict()
        codigos_procesados = []

        for freq in freq_codes.keys():
            all_codes = freq_codes.get(freq)
            codes, names_codes, _df_valid_codes, invalid = metadata.validate_codes(
                all_codes
            )
            codigos_procesados = codigos_procesados + codes
            limits = date_limits.get(freq)
            start_date_freq = limits.get("start_date")
            end_date_freq = limits.get("end_date")
            # cache
            cols_cached = bcrp_cache.cached_codes(freq, start_date_freq, end_date_freq)
            new_codes = [c for c in codes if c.upper() not in cols_cached]

            if new_codes:
                data_json = get_data_api(codes, start_date_freq, end_date_freq)
                df_freq = json_to_df(data_json, codes)
                df_freq = apply_date_format(df_freq, frequency=freq)
                df_freq = df_freq.rename(columns=names_codes)

                df_freq["date"] = df_freq["date"].astype(str)
                bcrp_cache.save(df_freq, freq, start_date_freq, end_date_freq)

            df_freq = bcrp_cache.load(freq, start_date_freq, end_date_freq, codes)
            df_freq = self.df_date_format(df_freq)
            result[freq] = df_freq

        self.valid_codes = codigos_procesados
        self.result = result
        # self.metadata_valid_codes = pd.concat(df_validos)
        return self

    def df_date_format(self, df):
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
        df["date"] = pd.to_datetime(df["date"])
        return df


if __name__ == "__main__":
    BCRPCache(CACHE_DB).clean_cache()
    series = BCRPSeries(
        [
            " RD16085DA",
            "PD04657MD",
            "PD04646PD",
            "RD13761DM",
            "RD13805DM",
            "RD13845DM",
            "RD15478DQ",
            "RD14266DQ",
            "CD10401DA",
            "CD10422DA",
            "fakea",
        ],
        start_date="2000-01-02",
        end_date="2020-01-01",
    )
    a = BCRPDataSeries(series).fetch_data()
    # print(a.metadata_valid_codes)
    from rich import print

    for freq in a.result.keys():
        print(freq)
        print(a.result.get(freq))

    series_adicionales = BCRPSeries(
        [
            " RD16085DA",
            "RD14266DQ",
            "fakea",
            # nuevos codigos
            "RD15238DQ",
            "RD15239DQ",
        ],
        start_date="2000-01-02",
        end_date="2023-01-01",
    )
    b = BCRPDataSeries(series_adicionales).fetch_data()
    print(b.result)
