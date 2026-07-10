"""
api.py
Task 3 - CRUD + time-series query endpoints for the stock time-series pipeline.

Exposes the SAME set of operations against both databases:
  MySQL   -> /sql/records/...
  MongoDB -> /mongo/records/...

Run locally:
    uvicorn api:app --reload

Interactive docs (Swagger UI) once running:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

from sql_routes import router as sql_router
from mongo_routes import router as mongo_router

app = FastAPI(
    title="Stock Time-Series Pipeline API",
    description=(
        "CRUD and time-series query endpoints (latest record, records by date "
        "range) for the synthetic multi-channel stock dataset, backed by both "
        "MySQL and MongoDB."
    ),
    version="1.0.0",
)

app.include_router(sql_router)
app.include_router(mongo_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Stock pipeline API is running"}
