"""
mongo_routes.py
CRUD + time-series query endpoints backed by MongoDB (stock_records collection,
same embedded-document shape used in load_mongo.py / migrate.py).
"""

from datetime import date
from typing import List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query

from db import get_mongo_collection
from models import StockRecordIn, StockRecordOut, StockRecordUpdate, PriceData, Indicators, Sentiment

router = APIRouter(prefix="/mongo/records", tags=["MongoDB"])


def _label_from_compound(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def _oid(record_id: str) -> ObjectId:
    try:
        return ObjectId(record_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid record id")


def _doc_to_out(doc: dict) -> StockRecordOut:
    return StockRecordOut(
        id=str(doc["_id"]),
        symbol=doc.get("symbol", "SYN1"),
        date=doc.get("date"),
        price=PriceData(**doc.get("price", {})),
        indicators=Indicators(**doc.get("indicators", {})),
        sentiment=Sentiment(**doc.get("sentiment", {})),
        target=doc.get("target"),
    )



@router.post("", response_model=StockRecordOut, status_code=201)
def create_record(record: StockRecordIn):
    collection = get_mongo_collection()

    sentiment = record.sentiment
    label = sentiment.label or _label_from_compound(sentiment.score)

    doc = {
        "symbol": record.symbol,
        "date": record.date.strftime("%Y-%m-%d"),
        "price": record.price.model_dump(),
        "indicators": record.indicators.model_dump(),
        "sentiment": {**sentiment.model_dump(), "label": label},
        "target": record.target,
    }
    result = collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_out(doc)

@router.get("/latest", response_model=StockRecordOut)
def get_latest_record(symbol: Optional[str] = Query(None)):
    collection = get_mongo_collection()
    query = {"symbol": symbol} if symbol else {}
    doc = collection.find_one(query, sort=[("date", -1)])
    if not doc:
        raise HTTPException(status_code=404, detail="No records found")
    return _doc_to_out(doc)


@router.get("/range", response_model=List[StockRecordOut])
def get_records_by_range(
    start_date: date = Query(..., description="Inclusive start date, YYYY-MM-DD"),
    end_date: date = Query(..., description="Inclusive end date, YYYY-MM-DD"),
    symbol: Optional[str] = Query(None),
):
    collection = get_mongo_collection()
    query = {"date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}}
    if symbol:
        query["symbol"] = symbol
    docs = collection.find(query).sort("date", 1)
    return [_doc_to_out(d) for d in docs]

@router.get("", response_model=List[StockRecordOut])
def list_records(
    symbol: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
):
    collection = get_mongo_collection()
    query = {"symbol": symbol} if symbol else {}
    docs = collection.find(query).sort("date", -1).skip(offset).limit(limit)
    return [_doc_to_out(d) for d in docs]

@router.get("/{record_id}", response_model=StockRecordOut)
def get_record(record_id: str):
    collection = get_mongo_collection()
    doc = collection.find_one({"_id": _oid(record_id)})
    if not doc:
        raise HTTPException(status_code=404, detail=f"record {record_id} not found")
    return _doc_to_out(doc)

@router.put("/{record_id}", response_model=StockRecordOut)
def update_record(record_id: str, update: StockRecordUpdate):
    collection = get_mongo_collection()
    oid = _oid(record_id)

    existing = collection.find_one({"_id": oid})
    if not existing:
        raise HTTPException(status_code=404, detail=f"record {record_id} not found")

    set_fields = {}
    if update.price:
        set_fields["price"] = update.price.model_dump()
    if update.indicators:
        set_fields["indicators"] = update.indicators.model_dump()
    if update.sentiment:
        s = update.sentiment
        label = s.label or _label_from_compound(s.score)
        set_fields["sentiment"] = {**s.model_dump(), "label": label}
    if update.target is not None:
        set_fields["target"] = update.target

    if set_fields:
        collection.update_one({"_id": oid}, {"$set": set_fields})

    doc = collection.find_one({"_id": oid})
    return _doc_to_out(doc)

@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: str):
    collection = get_mongo_collection()
    oid = _oid(record_id)
    result = collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"record {record_id} not found")
    return None
