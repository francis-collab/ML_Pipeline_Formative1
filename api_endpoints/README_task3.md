# Task 3 — CRUD & Time-Series API Endpoints

FastAPI service exposing the **same set of operations** against both databases
built in Task 2:

| Database | Base path       |
|----------|-----------------|
| MySQL    | `/sql/records`  |
| MongoDB  | `/mongo/records`|

## Setup

```bash
cd task3-api
pip install -r requirements.txt
cp .env.example .env      # then fill in your real MySQL / Mongo credentials
uvicorn api:app --reload
```

Swagger UI (interactive docs, lets you try every endpoint in the browser):
`http://127.0.0.1:8000/docs`

> **Do not commit `.env`.** Add it to `.gitignore`. Credentials should never be
> hardcoded in source files — the earlier scripts in `stock-pipeline-task2/`
> have real passwords committed; please rotate those and switch them to read
> from `.env` too before the final submission.

## Endpoints (identical shape for both `/sql` and `/mongo`)

| Method | Path                    | Description                                   |
|--------|-------------------------|------------------------------------------------|
| POST   | `/records`              | Create a new record                            |
| GET    | `/records`              | List records (`?symbol=&limit=&offset=`)       |
| GET    | `/records/latest`       | Most recent record (`?symbol=` optional)       |
| GET    | `/records/range`        | Records between two dates (`?start_date=&end_date=&symbol=`) |
| GET    | `/records/{id}`         | Get one record by id                           |
| PUT    | `/records/{id}`         | Partial update (price / indicators / sentiment / target) |
| DELETE | `/records/{id}`         | Delete a record                                |

`{id}` is the MySQL `price_id` (integer) for `/sql/records`, and the Mongo
`_id` (ObjectId string) for `/mongo/records`.

## Example requests

Create a record (works against either base path — just swap `sql`/`mongo`):
```bash
curl -X POST http://127.0.0.1:8000/sql/records \
  -H "Content-Type: application/json" \
  -d '{
        "symbol": "SYN1",
        "date": "2020-01-05",
        "price": {"open": 0.05, "high": 0.02, "low": 0.14, "close": 0.04, "volume": -1.1},
        "indicators": {"sma_10": 0.05, "rsi": 45.2, "macd": -0.13},
        "sentiment": {"headline": "Markets steady", "score": 0.12},
        "target": 1
      }'
```

Latest record for a symbol:
```bash
curl "http://127.0.0.1:8000/mongo/records/latest?symbol=SYN1"
```

Records in a date range:
```bash
curl "http://127.0.0.1:8000/sql/records/range?start_date=2020-01-01&end_date=2020-01-31&symbol=SYN1"
```

Update a record:
```bash
curl -X PUT http://127.0.0.1:8000/sql/records/1 \
  -H "Content-Type: application/json" \
  -d '{"target": 0}'
```

Delete a record:
```bash
curl -X DELETE http://127.0.0.1:8000/mongo/records/<object_id>
```

## Notes on implementation choices

- **MySQL**: `POST` writes across the three normalized tables (`price_history`,
  `technical_indicators`, `news_sentiment`) in one transaction, get-or-creating
  the `stocks` row by symbol. `DELETE` removes child rows first since the
  existing schema doesn't define `ON DELETE CASCADE`.
- **MongoDB**: CRUD operates directly on the embedded `stock_records` document
  shape already used in `load_mongo.py` / `migrate.py`.
- Connection credentials are pulled from environment variables via `db.py`
  (`python-dotenv`), not hardcoded — this was the one change made relative to
  the existing Task 2 scripts, for repo security.
