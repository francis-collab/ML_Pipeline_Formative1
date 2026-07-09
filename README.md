# Group6 Formative1 MLPipeline

# Task1 - Stock Market Price Movement Prediction

## Project Overview
Time-series Preprocessing, Exploratory Analysis & Modeling for a multivariate stock market dataset. The goal is to predict daily price movement (Up/Down/Stable) using technical indicators and temporal features.

**Contribution (Task 1)**: Full EDA, analytical questions, feature engineering, model experiments (3 classical ML models), visualizations, and best model selection.

---
## Task 2 - Database Design & Implementation

### What we did
For this part we took the same stock dataset from Task 1 and set it up in two 
different kinds of databases — MySQL (relational) and MongoDB (non-relational) — 
just to see how the same data looks and works in each one.

### MySQL side
Instead of putting everything into one giant table, we split it into four:

- **stocks** – basic info about the stock
- **price_history** – daily open/high/low/close/volume and the target we're predicting
- **technical_indicators** – SMA, EMA, RSI, MACD, Bollinger Bands, etc.
- **news_sentiment** – the day's headline plus its sentiment score/label

We separated indicators and sentiment from the raw price data since those are 
values we calculated ourselves, not stuff that came straight from the source — 
felt weird mixing "real" data with "computed" data in the same table. Everything's 
connected through `stock_id` and `price_id` foreign keys. The actual table 
definitions are in `database/schema.sql`, and there's an ERD image in 
`database/erd_diagram.png` if you want to see how it all connects.

### MongoDB side
For Mongo we didn't bother splitting things up — one document per trading day, 
with the price info, indicators, and sentiment all nested inside it in a single 
`stock_records` collection. Mongo doesn't do joins the same way SQL does, so it 
just made more sense to keep everything for a given day together in one place.

### Scripts we wrote
- `load_data.py` – loads the CSV into the MySQL tables
- `load_mongo.py` – loads the CSV directly into MongoDB
- `migrate.py` – takes what's already in MySQL and copies it over into MongoDB too, 
  so both databases end up with the same data

We kept passwords out of the actual files that get pushed — used placeholders 
instead so nobody's credentials end up on GitHub.

### Queries
Ran the 3 required queries on both databases (getting the latest record, pulling 
records from a date range, and one that looks at sentiment). Screenshots and 
results are in `database/queries_results.md`.

**What I worked on:** designed the schema, wrote `load_data.py`, `load_mongo.py`, 
and `migrate.py`, made the ERD, and ran all the queries on both databases.


---

# Task 3 - CRUD & Time-Series API Endpoints

## Overview
A FastAPI service exposing identical CRUD operations against **both** databases from Task 2, so either can be used interchangeably by Task 4's prediction script.

| Database | Base path         |
|----------|-------------------|
| MySQL    | `/sql/records`    |
| MongoDB  | `/mongo/records`  |

| Method | Path                | Description                                                   |
|--------|----------------------|----------------------------------------------------------------|
| POST   | `/records`           | Create a new record                                            |
| GET    | `/records`           | List records (`?symbol=&limit=&offset=`)                       |
| GET    | `/records/latest`    | Most recent record (`?symbol=` optional)                       |
| GET    | `/records/range`     | Records between two dates (`?start_date=&end_date=&symbol=`)   |
| GET    | `/records/{id}`      | Get one record by id                                           |
| PUT    | `/records/{id}`      | Partial update (price / indicators / sentiment / target)       |
| DELETE | `/records/{id}`      | Delete a record                                                 |

Credentials for both databases are read from a local `.env` file (never committed — see `.gitignore`), not hardcoded in source.

**Contribution (Task 3)**: `api.py`, `sql_routes.py`, `mongo_routes.py`, `db.py`, `models.py`, standalone data loaders (`load_data_local.py`, `load_mongo_local.py`) for independent local testing.

### Running the API
```bash
cd api_endpoints
pip install -r requirements.txt
cp .env
uvicorn api:app --reload
```
Interactive docs: `http://127.0.0.1:8000/docs`

---

# Task 4 - Prediction/Forecast Script
*(to be completed)*

Will fetch a record from the Task 3 API, apply the same preprocessing pipeline as Task 1, load `models/best_model.pkl`, and return a prediction.

---

## Repo Structure
```bash
ML_Pipeline_Formative1/
├── data/
│   └── stock_dataset.csv                          
├── notebooks/
│   └── Group6_Formative1_MLPipeline_Task1.ipynb    
├── stock-pipeline-task2/
│   ├── load_data.py                                 
│   ├── load_mongo.py                                 
│   └── migrate.py                                    
├── api_endpoints/                                    
│   ├── api.py
│   ├── db.py
│   ├── models.py
│   ├── sql_routes.py
│   ├── mongo_routes.py
│   ├── load_data_local.py
│   ├── load_mongo_local.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README_task3.md
├── models/
│   └── best_model.pkl                                
├── reports/
│   └── experiments.csv                              
├── database/                                         
│   ├── schema.sql
│   ├── erd_diagram.png
│   └── queries_results.md
├── README.md
└── .gitignore
```

## How to Run Task 1 Notebook
1. Upload `stock_dataset.csv` to Colab `data/` folder.
2. Open `Group6_Formative1_MLPipeline_Task1.ipynb`.


