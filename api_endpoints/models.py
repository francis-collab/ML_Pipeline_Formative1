"""
models.py
Pydantic schemas used by both the SQL and MongoDB endpoints. The shape mirrors
the fields already used in load_data.py / load_mongo.py so the same request
body can be sent to either /sql/records or /mongo/records.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PriceData(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float


class Indicators(BaseModel):
    sma_10: Optional[float] = None
    sma_20: Optional[float] = None
    ema_10: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    signal_line: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None


class Sentiment(BaseModel):
    headline: Optional[str] = None
    score: Optional[float] = None
    label: Optional[str] = None


class StockRecordIn(BaseModel):
    """Body used for creating a record (POST) in either database."""
    symbol: str = "SYN1"
    company_name: Optional[str] = "Synthetic Multi-Channel Stock"
    date: date
    price: PriceData
    indicators: Indicators = Field(default_factory=Indicators)
    sentiment: Sentiment = Field(default_factory=Sentiment)
    target: Optional[int] = None


class StockRecordUpdate(BaseModel):
    """Body used for PUT. Every field optional -> partial update."""
    price: Optional[PriceData] = None
    indicators: Optional[Indicators] = None
    sentiment: Optional[Sentiment] = None
    target: Optional[int] = None


class StockRecordOut(BaseModel):
    """Response shape returned by both /sql and /mongo endpoints."""
    id: str
    symbol: str
    date: str
    price: PriceData
    indicators: Indicators
    sentiment: Sentiment
    target: Optional[int] = None
