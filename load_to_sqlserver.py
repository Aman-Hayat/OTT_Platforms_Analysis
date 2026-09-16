import pandas as pd
from sqlalchemy import create_engine, text
import urllib
from pathlib import Path
from dotenv import load_dotenv
import os
load_dotenv()

# 1) sql server connections

SERVER = os.getenv('SQL_SERVER')
DATABASE = os.getenv('SQL_DATABASE')
DRIVER = os.getenv('SQL_DRIVER')
TRUSTED_CONNECTION = os.getenv('SQL_TRUSTED_CONNECTION')

conn_str = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection={TRUSTED_CONNECTION}'
params = urllib.parse.quote_plus(conn_str)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# 2) File Mapping

data_dir = Path("data")
csv_map = {
    "netflix": data_dir / "netflix_titles.csv",
    "amazon_prime": data_dir / "amazon_prime_titles.csv",
    "disney_plus": data_dir / "disney_plus_titles.csv",
}

# 3) Cleaning helper function

def df_cleaner(df):

    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace(".", "")
    )
    df["title"] = (
    df["title"]
    .str.strip()
    .str.lower()
    .str.replace(r"\s+", " ", regex=True))

    df["release_year"] = pd.to_numeric(
    df["release_year"],
    errors="coerce").astype("Int64")

    df = df.replace(r'^\s*$', pd.NA, regex=True)

    df = df.drop_duplicates(subset=["title", "release_year"], keep="first")

    if "date_added" in df.columns:
        df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")

    return df

for table_name, csv_path in csv_map.items():
    if csv_path.exists():
        print(f"\nProcessing {csv_path.name} -> dbo.{table_name}")
        df = pd.read_csv(csv_path)
        df = df_cleaner(df)

        print("Null counts:")
        print(df.isna().sum())
        
        df.to_sql(
            name=table_name,
            con=engine,
            schema="dbo",
            if_exists="replace",
            index=False,
            chunksize=150,
            method="multi",
        )

        print("\nAll source tables loaded.")
    else:
        print(f"File {csv_path} does not exist.")

combined_sql = """
IF OBJECT_ID('dbo.ott_content', 'U') IS NOT NULL
    DROP TABLE dbo.ott_content;

SELECT *, 'Netflix' AS platform
INTO dbo.ott_content
FROM dbo.netflix

UNION ALL

SELECT *, 'Prime Video' AS platform
FROM dbo.amazon_prime

UNION ALL

SELECT *, 'Disney+' AS platform
FROM dbo.disney_plus;
"""

with engine.begin() as conn:
    conn.execute(text(combined_sql))

print("dbo.ott_content created successfully.")

