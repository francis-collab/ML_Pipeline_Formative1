# Group6 Formative1 MLPipeline

# Task1 - Stock Market Price Movement Prediction

## Project Overview
Time-series Preprocessing, Exploratory Analysis & Modeling for a multivariate stock market dataset. The goal is to predict daily price movement (Up/Down/Stable) using technical indicators and temporal features.

**Contribution (Task 1)**: Full EDA, analytical questions, feature engineering, model experiments (3 classical ML models), visualizations, and best model selection.

---

# Task 2 - Database Design & Implementation

## Overview
Designed and implemented both a relational (MySQL) and non-relational (MongoDB) representation of the same stock time-series dataset.

- **MySQL**: normalized schema across four tables — `stocks`, `price_history`, `technical_indicators`, `news_sentiment` — linked by `stock_id` / `price_id` foreign keys. Schema defined in `database/schema.sql`.
- **MongoDB**: a single `stock_records` collection with `price`, `indicators`, and `sentiment` embedded as sub-documents per record.
- `migrate.py` moves data from the MySQL tables into the MongoDB collection to keep both databases in sync.

**Contribution (Task 2)**: Schema design, MySQL loading script (`load_data.py`), MongoDB loading script (`load_mongo.py`), migration script (`migrate.py`).

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


