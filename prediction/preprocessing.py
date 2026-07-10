"""
preprocessing.py (task 4)
rebuilds the task 1 preprocessing + feature engineering pipeline,
just starting from the task 3 api records instead of the raw csv.
does the missing value handling (time interpolate then forward fill),
then builds the lag/rolling/date features same as the notebook.
one extra thing: the task 1 model was trained on the
Sentiment_Pos/Neg/Neu columns but the databases only keep the
headline and compound score. we checked and those columns are just
the vader scores of the headline (all 1000 rows matched), so we
recompute them here with the same vader analyzer.
"""
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# reuse one analyzer for every row, loading the lexicon is the slow part
_ANALYZER = SentimentIntensityAnalyzer()


def _sentiment_features(headline, stored_compound):
    """recompute the 4 vader sentiment columns we used at training time.
    if a record has no headline just fall back to a neutral split (and reuse
    the stored compound score if theres one)
    """
    if headline:
        scores = _ANALYZER.polarity_scores(headline)
        return scores["pos"], scores["neg"], scores["neu"], scores["compound"]
    compound = stored_compound if stored_compound is not None else 0.0
    return 0.0, 0.0, 1.0, compound


def records_to_frame(records):
    """turn the list of task 3 api records (dicts, StockRecordOut shape) into a
    dataframe with the same columns/layout as the task 1 csv."""
    rows = []
    for rec in records:
        price = rec.get("price") or {}
        ind = rec.get("indicators") or {}
        sent = rec.get("sentiment") or {}
        pos, neg, neu, compound = _sentiment_features(
            sent.get("headline"), sent.get("score")
        )
        rows.append(
            {
                "Date": rec["date"],
                "Open": price.get("open"),
                "High": price.get("high"),
                "Low": price.get("low"),
                "Close": price.get("close"),
                "Volume": price.get("volume"),
                "SMA_10": ind.get("sma_10"),
                "SMA_20": ind.get("sma_20"),
                "EMA_10": ind.get("ema_10"),
                "RSI": ind.get("rsi"),
                "MACD": ind.get("macd"),
                "Signal": ind.get("signal_line"),
                "BB_Middle": ind.get("bb_middle"),
                "BB_Upper": ind.get("bb_upper"),
                "BB_Lower": ind.get("bb_lower"),
                "Sentiment_Pos": pos,
                "Sentiment_Neg": neg,
                "Sentiment_Neu": neu,
                "Sentiment_Compound": compound,
                "Target": rec.get("target"),
            }
        )
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    # records with null indicators (like the first few days before SMA_20 exists)
    # come in as None and make object columns, which pandas 2 wont interpolate,
    # so push everything to numeric first
    df = df.apply(pd.to_numeric, errors="coerce")
    # drop same day duplicates (test rows we posted during the task 3 demos)
    # otherwise they mess up the shift/rolling stuff, keep the last one per day
    df = df[~df.index.duplicated(keep="last")]
    return df


def handle_missing(df):
    """missing value handling from task 1, make a proper utc index then
    time interpolate and forward fill."""
    df = df.copy()
    df.index = pd.to_datetime(df.index, utc=True, errors="coerce")
    df = df.interpolate(method="time")
    df = df.ffill()
    return df


def create_features(df):
    """feature engineering from the task 1 notebook (the analytical question
    features plus create_features())."""
    df = df.copy()
    # features we made while answering questions Q3/Q4
    df["lag_1"] = df["Close"].shift(1)
    df["ma_5"] = df["Close"].rolling(5, min_periods=1).mean()
    # the create_features() bit from the feature engineering cell
    df["dayofweek"] = df.index.dayofweek
    df["month"] = df.index.month
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    for lag in [1, 5]:
        df[f"lag_{lag}"] = df["Close"].shift(lag)
    df["rolling_mean_5"] = df["Close"].rolling(5, min_periods=1).mean()
    df["rolling_std_5"] = df["Close"].rolling(5, min_periods=1).std()
    return df


def preprocess_records(records):
    """the whole task 1 pipeline: api records -> a model ready dataframe.
    gives back the engineered dataframe (still has cllose in it, only used to
    build the lag/rolling features, the caller picks out the model columns).
    """
    df = records_to_frame(records)
    df = handle_missing(df)
    df = create_features(df)
    return df