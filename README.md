"""
load_data_local.py
Standalone copy of stock-pipeline-task2/load_data.py, adapted to read
credentials from .env instead of being hardcoded, and to run from the
task3-api/ folder without touching your teammate's original files.

Usage:
    cd task3-api
    python load_data_local.py
"""

import os
import pandas as pd
import numpy as np
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Path to the dataset - adjust if you keep your own copy elsewhere.
# Defaults to the shared copy in stock-pipeline-task2/ (read-only access,
# no editing of that folder needed).
DATA_PATH = os.getenv("STOCK_CSV_PATH", "../stock-pipeline-task2/stock_dataset.csv")

# ---- 1. Connect to MySQL (credentials from .env) ----
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE", "stock_pipeline"),
)
cursor = conn.cursor()

# ---- 2. Load and clean the CSV ----
df = pd.read_csv(DATA_PATH)
df["Date"] = pd.to_datetime(df["Date"])
df = df.replace({np.nan: None})

# Reuse the stock row if this script is re-run, instead of duplicating it
cursor.execute("SELECT stock_id FROM stocks WHERE symbol = %s", ("SYN1",))
existing = cursor.fetchone()
if existing:
    stock_id = existing[0]
else:
    cursor.execute(
        "INSERT INTO stocks (symbol, company_name) VALUES (%s, %s)",
        ("SYN1", "Synthetic Multi-Channel Stock")
    )
    conn.commit()
    stock_id = cursor.lastrowid
print(f"Using stock_id={stock_id}")

# ---- 3. Insert each row into price_history, technical_indicators, news_sentiment ----
price_sql = """
    INSERT INTO price_history
        (stock_id, trade_date, open_price, high_price, low_price, close_price, volume, target)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
indicator_sql = """
    INSERT INTO technical_indicators
        (price_id, sma_10, sma_20, ema_10, rsi, macd, signal_line, bb_middle, bb_upper, bb_lower)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
sentiment_sql = """
    INSERT INTO news_sentiment
        (price_id, headline, sentiment_score, sentiment_label)
    VALUES (%s, %s, %s, %s)
"""

def label_from_compound(score):
    if score is None:
        return None
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    return "neutral"

inserted = 0
for _, row in df.iterrows():
    cursor.execute(price_sql, (
        stock_id,
        row["Date"].date(),
        row["Open"], row["High"], row["Low"], row["Close"],
        row["Volume"], int(row["Target"])
    ))
    price_id = cursor.lastrowid

    cursor.execute(indicator_sql, (
        price_id,
        row["SMA_10"], row["SMA_20"], row["EMA_10"], row["RSI"],
        row["MACD"], row["Signal"], row["BB_Middle"], row["BB_Upper"], row["BB_Lower"]
    ))

    cursor.execute(sentiment_sql, (
        price_id,
        row["Clean_Headline"],
        row["Sentiment_Compound"],
        label_from_compound(row["Sentiment_Compound"])
    ))

    inserted += 1

conn.commit()
print(f"Inserted {inserted} rows into price_history, technical_indicators, news_sentiment.")

cursor.close()
conn.close()