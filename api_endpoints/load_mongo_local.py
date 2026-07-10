"""
load_mongo_local.py
Standalone copy of stock-pipeline-task2/load_mongo.py, adapted to read
the connection string from .env instead of being hardcoded, and to run
from the task3-api/ folder without touching your teammate's original files.

Usage:
    cd task3-api
    python load_mongo_local.py
"""

import os
import pandas as pd
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = os.getenv("STOCK_CSV_PATH", "../stock-pipeline-task2/stock_dataset.csv")


CONNECTION_STRING = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(CONNECTION_STRING)
db = client[os.getenv("MONGO_DATABASE", "stock_pipeline")]
collection = db["stock_records"]


df = pd.read_csv(DATA_PATH)
df["Date"] = pd.to_datetime(df["Date"])
df = df.replace({np.nan: None})

def label_from_compound(score):
    if score is None:
        return None
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    return "neutral"


documents = []
for _, row in df.iterrows():
    doc = {
        "symbol": "SYN1",
        "date": row["Date"].strftime("%Y-%m-%d"),
        "price": {
            "open": row["Open"],
            "high": row["High"],
            "low": row["Low"],
            "close": row["Close"],
            "volume": row["Volume"],
        },
        "indicators": {
            "sma_10": row["SMA_10"],
            "sma_20": row["SMA_20"],
            "ema_10": row["EMA_10"],
            "rsi": row["RSI"],
            "macd": row["MACD"],
            "signal_line": row["Signal"],
            "bb_middle": row["BB_Middle"],
            "bb_upper": row["BB_Upper"],
            "bb_lower": row["BB_Lower"],
        },
        "sentiment": {
            "headline": row["Clean_Headline"],
            "score": row["Sentiment_Compound"],
            "label": label_from_compound(row["Sentiment_Compound"]),
        },
        "target": int(row["Target"]),
    }
    documents.append(doc)


collection.delete_many({})
result = collection.insert_many(documents)
print(f"Inserted {len(result.inserted_ids)} documents into stock_records.")

