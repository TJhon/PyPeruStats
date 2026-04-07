import time

import pandas as pd
from tqdm import tqdm

from perustats.BCRP.archive.constants import DATE_RANGES, RELEASES, SERIES_TABLE
from perustats.BCRP.archive.utils import get_connection
from perustats.BCRP.fetcher import BCRPDataProcessor

conn = get_connection()

df = pd.read_sql(f"select codigo, grupo_file from {SERIES_TABLE}", con=conn)
groups = df["grupo_file"].drop_duplicates()

for group, df in tqdm(df.groupby("grupo_file"), total=len(groups)):
    try:
        freq = group.split("_")[1]
        codes = df["codigo"].tolist()
        result = BCRPDataProcessor(
            codes, start_date=DATE_RANGES[0], end_date=DATE_RANGES[1]
        ).process_data()
        df_freq = result.get(freq)
        RELEASES.mkdir(parents=True, exist_ok=True)
        path = RELEASES / f"{group}.parquet"
        df_freq.to_parquet(path, index=False, engine="pyarrow")
    except Exception:
        print(group)
    time.sleep(1)
