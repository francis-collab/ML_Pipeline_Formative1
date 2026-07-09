"""
db.py
Connection helpers for both databases used in the stock time-series pipeline.

Credentials are read from environment variables (see .env.example) instead of
being hardcoded, so this file is safe to commit to GitHub.
"""

import os
from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "stock_pipeline")

_mysql_pool = pooling.MySQLConnectionPool(
    pool_name="stock_pool",
    pool_size=5,
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE,
)


@contextmanager
def get_mysql_conn():
    """Yields a pooled MySQL connection, always returned to the pool after use."""
    conn = _mysql_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "stock_pipeline")

_mongo_client = MongoClient(MONGO_URI)
_mongo_db = _mongo_client[MONGO_DATABASE]


def get_mongo_collection():
    return _mongo_db["stock_records"]
