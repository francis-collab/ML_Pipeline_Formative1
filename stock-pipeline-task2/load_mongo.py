import pandas as pd
import numpy as np
from pymongo import MongoClient

# ---- 1. Connect to Atlas ----
CONNECTION_STRING = "mongodb+srv:Berissa@123@cluster0.vbtebyo.mongodb.net/?appName=Cluster0"
client = MongoClient(CONNECTION_STRING)
db = client["stock_pipeline"]
collection = db["stock_records"]

# ---- 2. Load and clean CSV ----
df = pd.read_csv("stock_dataset.csv")
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

# ---- 3. Build documents ----
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

# ---- 4. Insert ----
result = collection.insert_many(documents)
print(f"Inserted {len(result.inserted_ids)} documents into stock_records.")