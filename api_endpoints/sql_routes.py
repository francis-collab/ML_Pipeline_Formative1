"""
sql_routes.py
CRUD + time-series query endpoints backed by MySQL
(tables: stocks, price_history, technical_indicators, news_sentiment).
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from db import get_mysql_conn
from models import StockRecordIn, StockRecordOut, StockRecordUpdate, PriceData, Indicators, Sentiment

router = APIRouter(prefix="/sql/records", tags=["MySQL"])


def _label_from_compound(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def _get_or_create_stock(cursor, symbol: str, company_name: Optional[str]) -> int:
    cursor.execute("SELECT stock_id FROM stocks WHERE symbol = %s", (symbol,))
    row = cursor.fetchone()
    if row:
        return row["stock_id"] if isinstance(row, dict) else row[0]
    cursor.execute(
        "INSERT INTO stocks (symbol, company_name) VALUES (%s, %s)",
        (symbol, company_name),
    )
    return cursor.lastrowid


def _row_to_out(row: dict) -> StockRecordOut:
    return StockRecordOut(
        id=str(row["price_id"]),
        symbol=row["symbol"],
        date=str(row["trade_date"]),
        price=PriceData(
            open=row["open_price"], high=row["high_price"],
            low=row["low_price"], close=row["close_price"], volume=row["volume"],
        ),
        indicators=Indicators(
            sma_10=row.get("sma_10"), sma_20=row.get("sma_20"), ema_10=row.get("ema_10"),
            rsi=row.get("rsi"), macd=row.get("macd"), signal_line=row.get("signal_line"),
            bb_middle=row.get("bb_middle"), bb_upper=row.get("bb_upper"), bb_lower=row.get("bb_lower"),
        ),
        sentiment=Sentiment(
            headline=row.get("headline"), score=row.get("sentiment_score"), label=row.get("sentiment_label"),
        ),
        target=row.get("target"),
    )


JOIN_SELECT = """
    SELECT
        p.price_id, s.symbol, p.trade_date, p.open_price, p.high_price,
        p.low_price, p.close_price, p.volume, p.target,
        t.sma_10, t.sma_20, t.ema_10, t.rsi, t.macd, t.signal_line,
        t.bb_middle, t.bb_upper, t.bb_lower,
        n.headline, n.sentiment_score, n.sentiment_label
    FROM price_history p
    JOIN stocks s ON p.stock_id = s.stock_id
    LEFT JOIN technical_indicators t ON p.price_id = t.price_id
    LEFT JOIN news_sentiment n ON p.price_id = n.price_id
"""


# ---------------------------------------------------------------------------
# POST /sql/records  - create
# ---------------------------------------------------------------------------
@router.post("", response_model=StockRecordOut, status_code=201)
def create_record(record: StockRecordIn):
    with get_mysql_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            stock_id = _get_or_create_stock(cursor, record.symbol, record.company_name)

            cursor.execute(
                """INSERT INTO price_history
                       (stock_id, trade_date, open_price, high_price, low_price, close_price, volume, target)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (stock_id, record.date, record.price.open, record.price.high,
                 record.price.low, record.price.close, record.price.volume, record.target),
            )
            price_id = cursor.lastrowid

            ind = record.indicators
            cursor.execute(
                """INSERT INTO technical_indicators
                       (price_id, sma_10, sma_20, ema_10, rsi, macd, signal_line, bb_middle, bb_upper, bb_lower)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (price_id, ind.sma_10, ind.sma_20, ind.ema_10, ind.rsi, ind.macd,
                 ind.signal_line, ind.bb_middle, ind.bb_upper, ind.bb_lower),
            )

            sent = record.sentiment
            label = sent.label or _label_from_compound(sent.score)
            cursor.execute(
                """INSERT INTO news_sentiment (price_id, headline, sentiment_score, sentiment_label)
                   VALUES (%s, %s, %s, %s)""",
                (price_id, sent.headline, sent.score, label),
            )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            cursor.close()

    return get_record(price_id)


# ---------------------------------------------------------------------------
# GET /sql/records/latest  - latest record (must be declared before /{price_id})
# ---------------------------------------------------------------------------
@router.get("/latest", response_model=StockRecordOut)
def get_latest_record(symbol: Optional[str] = Query(None, description="Filter by stock symbol")):
    with get_mysql_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        sql = JOIN_SELECT
        params = ()
        if symbol:
            sql += " WHERE s.symbol = %s"
            params = (symbol,)
        sql += " ORDER BY p.trade_date DESC LIMIT 1"
        cursor.execute(sql, params)
        row = cursor.fetchone()
        cursor.close()

    if not row:
        raise HTTPException(status_code=404, detail="No records found")
    return _row_to_out(row)


# ---------------------------------------------------------------------------
# GET /sql/records/range  - records by date range
# ---------------------------------------------------------------------------
@router.get("/range", response_model=List[StockRecordOut])
def get_records_by_range(
    start_date: date = Query(..., description="Inclusive start date, YYYY-MM-DD"),
    end_date: date = Query(..., description="Inclusive end date, YYYY-MM-DD"),
    symbol: Optional[str] = Query(None),
):
    with get_mysql_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        sql = JOIN_SELECT + " WHERE p.trade_date BETWEEN %s AND %s"
        params = [start_date, end_date]
        if symbol:
            sql += " AND s.symbol = %s"
            params.append(symbol)
        sql += " ORDER BY p.trade_date ASC"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

    return [_row_to_out(r) for r in rows]


# ---------------------------------------------------------------------------
# GET /sql/records  - list (paginated)
# ---------------------------------------------------------------------------
@router.get("", response_model=List[StockRecordOut])
def list_records(
    symbol: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
):
    with get_mysql_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        sql = JOIN_SELECT
        params = []
        if symbol:
            sql += " WHERE s.symbol = %s"
            params.append(symbol)
        sql += " ORDER BY p.trade_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

    return [_row_to_out(r) for r in rows]


# ---------------------------------------------------------------------------
# GET /sql/records/{price_id}  - read one
# ---------------------------------------------------------------------------
@router.get("/{price_id}", response_model=StockRecordOut)
def get_record(price_id: int):
    with get_mysql_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(JOIN_SELECT + " WHERE p.price_id = %s", (price_id,))
        row = cursor.fetchone()
        cursor.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"price_id {price_id} not found")
    return _row_to_out(row)


# ---------------------------------------------------------------------------
# PUT /sql/records/{price_id}  - partial update
# ---------------------------------------------------------------------------
@router.put("/{price_id}", response_model=StockRecordOut)
def update_record(price_id: int, update: StockRecordUpdate):
    with get_mysql_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT price_id FROM price_history WHERE price_id = %s", (price_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail=f"price_id {price_id} not found")

        try:
            if update.price:
                p = update.price
                cursor.execute(
                    """UPDATE price_history
                       SET open_price=%s, high_price=%s, low_price=%s, close_price=%s, volume=%s
                       WHERE price_id=%s""",
                    (p.open, p.high, p.low, p.close, p.volume, price_id),
                )
            if update.target is not None:
                cursor.execute(
                    "UPDATE price_history SET target=%s WHERE price_id=%s",
                    (update.target, price_id),
                )
            if update.indicators:
                i = update.indicators
                cursor.execute(
                    """UPDATE technical_indicators
                       SET sma_10=%s, sma_20=%s, ema_10=%s, rsi=%s, macd=%s,
                           signal_line=%s, bb_middle=%s, bb_upper=%s, bb_lower=%s
                       WHERE price_id=%s""",
                    (i.sma_10, i.sma_20, i.ema_10, i.rsi, i.macd,
                     i.signal_line, i.bb_middle, i.bb_upper, i.bb_lower, price_id),
                )
            if update.sentiment:
                s = update.sentiment
                label = s.label or _label_from_compound(s.score)
                cursor.execute(
                    """UPDATE news_sentiment
                       SET headline=%s, sentiment_score=%s, sentiment_label=%s
                       WHERE price_id=%s""",
                    (s.headline, s.score, label, price_id),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            cursor.close()

    return get_record(price_id)


# ---------------------------------------------------------------------------
# DELETE /sql/records/{price_id}
# ---------------------------------------------------------------------------
@router.delete("/{price_id}", status_code=204)
def delete_record(price_id: int):
    with get_mysql_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT price_id FROM price_history WHERE price_id = %s", (price_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail=f"price_id {price_id} not found")

        try:
            # child rows first (no ON DELETE CASCADE assumed on the FKs)
            cursor.execute("DELETE FROM news_sentiment WHERE price_id=%s", (price_id,))
            cursor.execute("DELETE FROM technical_indicators WHERE price_id=%s", (price_id,))
            cursor.execute("DELETE FROM price_history WHERE price_id=%s", (price_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            cursor.close()

    return None
