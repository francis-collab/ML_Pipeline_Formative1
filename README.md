# Group6 Formative1 MLPipeline

# Task1 - Stock Market Price Movement Prediction

## Project Overview
Time-series Preprocessing, Exploratory Analysis & Modeling for a multivariate stock market dataset. The goal is to predict daily price movement (Up/Down/Stable) using technical indicators and temporal features.

**Contribution (Task 1)**: Full EDA, analytical questions, feature engineering, model experiments (3 classical ML models), visualizations, and best model selection.

## How to Run Task 1 Notebook
1. Upload `stock_dataset.csv` to Colab `data/` folder.
2. Open `Group6_Formative1_MLPipeline_Task1.ipynb`.
3. Run cells sequentially (Imports → EDA → Feature Engineering → Experiments → Testing).

## Key Results (Task 1)
- **Best Model**: Tuned XGBoost (Accuracy ~0.845, F1 ~0.820 on cross-validation)
- **Test Set Performance**: Accuracy 0.858, F1 0.818 on unseen data
- Strong performance on Up/Down movements; Stable class is harder due to market noise (expected).

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
# task 4 - prediction script

## overview
`prediction/predict.py` just ties tasks 1 to 3 together into one script that makes a forecast:

1. **fetch** - grabs the anchor record from the task 3 api (`/records/latest`), then its last 30 days of history from `/records/range`. works with either backend (`--source sql` or `--source mongo`).
2. **preprocess** - `prediction/preprocessing.py` redoes the same task 1 pipeline on that window, time interpolate + forward fill for the missing values, then builds the features (`lag_1`, `lag_5`, `ma_5`, `rolling_mean_5`, `rolling_std_5`, `dayofweek`, `month`, `is_weekend`).
3. **load model** - loads the xgboost model from `models/best_model.pkl` and lines the columns up to match what it trained on (`feature_names_in_`).
4. **predict** - spits out the next day price movement (down / stable / up) with the probabilities.

### the sentiment thing
the task 1 model was trained on the `Sentiment_Pos/Neg/Neu/Compound` columns, but the task 2 databases only keep the headline, compound score and label. we checked and those sentiment columns are just the vader scores of `Clean_Headline` (all 1000 rows matched), so the script recomputes them from the headline the api gives back, same values the model saw when it trained.

### how to run it
```bash
# start the task 3 api first (see the task 3 section above)
cd prediction
pip install -r requirements.txt
python predict.py                    # latest record, mysql
python predict.py --source mongo     # same but from mongodb
python predict.py --date 2022-06-15  # a specific date
```

what it looks like when you run it:
```
==============================================================
task 4 - stock price movement forecast
==============================================================
[fetch] got latest record from /sql/records/latest -> 2023-10-31
[fetch] pulled 22 records from /sql/records/range (2023-10-01 .. 2023-10-31)
[prep] made 27 columns over 22 days
[model] loaded XGBClassifier from models/best_model.pkl
--------------------------------------------------------------
anchor record: 2023-10-31  (source: SQL)
forecast: next day price movement = DOWN
probabilities: Down=0.994  Stable=0.004  Up=0.002
==============================================================
```

running it with `--source mongo` gives the same forecast, we checked that the features from the api match the notebook to within 1e-14 and both backends give back the same records.

**contribution (task 4)**: `prediction/predict.py`, `prediction/preprocessing.py`, the sentiment reconstruction bit, and testing it end to end against both databases.

---

## repo structure
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
├── prediction/                                       
│   ├── predict.py
│   ├── preprocessing.py
│   └── requirements.txt
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


