"""
predict.py (task 4 - prediction script)
ties task 1 to 3 together. it fetches the time series data from the task 3 fastapi service (mysql or mongo, pick with --source), redoes the task 1 preprocessing and features on that window (see preprocessing.py), loads the xgboost model from task 1 (models/best_model.pkl), then predicts the next day price move (down / stable / up) with probabilities.
how to run (api needs to be up first, see api_endpoints/README):
python predict.py -> latest record, mysql
python predict.py --source mongo -> latest record, mongo
python predict.py --date 2022-06-15 -> a specific day
python predict.py --api-url http://127.0.0.1:8000 --symbol SYN1
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
import joblib
import pandas as pd
import requests
from preprocessing import preprocess_records

CLASS_NAMES = {0: "Down", 1: "Stable", 2: "Up"}
HISTORY_DAYS = 30
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "best_model.pkl"


def fetch_records(api_url, source, symbol, anchor_date=None):
    """grabs the anchor record plus its trailing history window from the api,
    returns (records, anchor_date_str). uses /records/latest when no date is passed,
    then /records/range to get the history window, those are the two time series
    endpoints from task 3.
    """
    base = f"{api_url.rstrip('/')}/{source}/records"
    params = {"symbol": symbol} if symbol else {}
    if anchor_date is None:
        resp = requests.get(f"{base}/latest", params=params, timeout=10)
        resp.raise_for_status()
        anchor_date = resp.json()["date"]
        print(f"[fetch] got latest record from /{source}/records/latest -> {anchor_date}")
    anchor = datetime.strptime(anchor_date, "%Y-%m-%d").date()
    start = anchor - timedelta(days=HISTORY_DAYS)
    resp = requests.get(
        f"{base}/range",
        params={"start_date": start.isoformat(), "end_date": anchor.isoformat(), **params},
        timeout=30,
    )
    resp.raise_for_status()
    records = resp.json()
    print(f"[fetch] pulled {len(records)} records from /{source}/records/range "
          f"({start} .. {anchor})")
    return records, anchor_date


def load_model(model_path):
    model = joblib.load(model_path)
    print(f"[model] loaded {type(model).__name__} from {model_path}")
    return model


def predict_movement(model, features, anchor_date):
    """picks the anchor row, lines up the columns to match what the model
    trained on, then makes the next day movement forecast."""
    # line the columns up with the exact names/order the model was trained on
    X = features.reindex(columns=model.feature_names_in_)
    row = X.loc[X.index.strftime("%Y-%m-%d") == anchor_date]
    if row.empty:
        sys.exit(f"oops, no feature row for {anchor_date} after preprocessing")
    if row.isna().any(axis=None):
        missing = row.columns[row.isna().any()].tolist()
        sys.exit(f"oops, features {missing} came out NaN for {anchor_date}, "
                 f"probably not enough history before this date")
    pred = int(model.predict(row)[0])
    proba = model.predict_proba(row)[0]
    return pred, proba


def main():
    parser = argparse.ArgumentParser(description="task 4 prediction script")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000",
                        help="base url of the task 3 api")
    parser.add_argument("--source", choices=["sql", "mongo"], default="sql",
                        help="which db backend to pull from")
    parser.add_argument("--symbol", default="SYN1", help="stock symbol")
    parser.add_argument("--date", default=None,
                        help="anchor date YYYY-MM-DD (default is latest record)")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH),
                        help="path to the trained model pickle")
    args = parser.parse_args()

    print("=" * 62)
    print("task 4 - stock price movement forecast")
    print("=" * 62)

    # 1. geting the time series records from the task 3 api
    try:
        records, anchor_date = fetch_records(args.api_url, args.source,
                                             args.symbol, args.date)
    except requests.ConnectionError:
        sys.exit(f"cant reach the api at {args.api_url}, start it first "
                 f"with: cd api_endpoints && uvicorn api:app --reload")
    except requests.HTTPError as exc:
        sys.exit(f"api request failed: {exc}")
    if not records:
        sys.exit("the api gave back no records for that date range")

    # 2. run it through the task 1 preprocessing
    features = preprocess_records(records)
    print(f"[prep] made {features.shape[1]} columns over {features.shape[0]} days")

    # 3. load the trained task 1 model
    model = load_model(args.model)

    # 4. predict next day price movement
    pred, proba = predict_movement(model, features, anchor_date)

    print("-" * 62)
    print(f"anchor record: {anchor_date}  (source: {args.source.upper()})")
    print(f"forecast: next day price movement = {CLASS_NAMES[pred].upper()}")
    print("probabilities: " + "  ".join(
        f"{CLASS_NAMES[i]}={p:.3f}" for i, p in enumerate(proba)))
    print("=" * 62)


if __name__ == "__main__":
    main()