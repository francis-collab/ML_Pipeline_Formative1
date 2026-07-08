import mysql.connector
import pymongo

mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Umurerw@1",
    database="stock_pipeline"
)
mysql_cursor = mysql_conn.cursor(dictionary=True)

query = """
SELECT 
    s.symbol, p.trade_date, p.open_price, p.high_price, 
    p.low_price, p.close_price, p.volume,
    t.rsi, t.macd, n.sentiment_label, n.sentiment_score
FROM price_history p
JOIN stocks s ON p.stock_id = s.stock_id
LEFT JOIN technical_indicators t ON p.price_id = t.price_id
LEFT JOIN news_sentiment n ON p.price_id = n.price_id;
"""

mysql_cursor.execute(query)
records = mysql_cursor.fetchall()

mongo_documents = []
for row in records:
    doc = {
        "symbol": row["symbol"],
        "date": str(row["trade_date"]),
        "price": {
            "open": float(row["open_price"]) if row["open_price"] is not None else 0.0,
            "high": float(row["high_price"]) if row["high_price"] is not None else 0.0,
            "low": float(row["low_price"]) if row["low_price"] is not None else 0.0,
            "close": float(row["close_price"]) if row["close_price"] is not None else 0.0,
            "volume": int(row["volume"]) if row["volume"] is not None else 0
        },
        "indicators": {
            "rsi": float(row["rsi"]) if row["rsi"] is not None else None,
            "macd": float(row["macd"]) if row["macd"] is not None else None
        },
        "sentiment": {
            "label": row["sentiment_label"] if row["sentiment_label"] is not None else "neutral",
            "score": float(row["sentiment_score"]) if row["sentiment_score"] is not None else 0.0
        }
    }
    mongo_documents.append(doc)

# ---- Insert into MongoDB Atlas ----
mongo_uri = "mongodb+srv://stockuser:T6SxVfhCWTvKjOfN@cluster0.blype8i.mongodb.net/?retryWrites=true&w=majority"
mongo_client = pymongo.MongoClient(mongo_uri)
db = mongo_client["stock_pipeline"]
collection = db["stock_records"]

collection.delete_many({})  # clear old entries, safe to re-run
result = collection.insert_many(mongo_documents)

print(f"Successfully migrated {len(result.inserted_ids)} documents to MongoDB Atlas!")

mysql_cursor.close()
mysql_conn.close()
mongo_client.close()