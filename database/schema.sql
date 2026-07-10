-- ============================================================
-- Task 2: Relational Database Schema (MySQL)
-- Dataset: Multi-Channel Stock Market Dataset (Kaggle)
-- ============================================================

CREATE DATABASE IF NOT EXISTS stock_pipeline;
USE stock_pipeline;

-- Drop tables in reverse dependency order (safe to re-run)
DROP TABLE IF EXISTS news_sentiment;
DROP TABLE IF EXISTS technical_indicators;
DROP TABLE IF EXISTS price_history;
DROP TABLE IF EXISTS stocks;

-- ------------------------------------------------------------
-- Table 1: stocks
-- One row per traded symbol. Our CSV covers a single synthetic
-- symbol, but the table is designed to scale to many.
-- ------------------------------------------------------------
CREATE TABLE stocks (
    stock_id      INT AUTO_INCREMENT PRIMARY KEY,
    symbol        VARCHAR(10)  NOT NULL UNIQUE,
    company_name  VARCHAR(150) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table 2: price_history
-- Core daily OHLCV time-series table. One row per (stock, date).
-- ------------------------------------------------------------
CREATE TABLE price_history (
    price_id     INT AUTO_INCREMENT PRIMARY KEY,
    stock_id     INT NOT NULL,
    trade_date   DATE NOT NULL,
    open_price   DOUBLE NOT NULL,
    high_price   DOUBLE NOT NULL,
    low_price    DOUBLE NOT NULL,
    close_price  DOUBLE NOT NULL,
    volume       DOUBLE NOT NULL,
    target       TINYINT NOT NULL,  -- 1 = price goes up next period, 0 = down
    CONSTRAINT fk_price_stock FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_stock_date UNIQUE (stock_id, trade_date)
);

CREATE INDEX idx_price_date ON price_history(trade_date);

-- ------------------------------------------------------------
-- Table 3: technical_indicators
-- One-to-one with price_history. Kept separate from price_history
-- because these are derived features (rolling windows), not
-- raw observations -- separating them keeps the raw price table
-- clean and makes it obvious which columns are engineered.
-- ------------------------------------------------------------
CREATE TABLE technical_indicators (
    indicator_id  INT AUTO_INCREMENT PRIMARY KEY,
    price_id      INT NOT NULL UNIQUE,
    sma_10        DOUBLE,
    sma_20        DOUBLE,
    ema_10        DOUBLE,
    rsi           DOUBLE,
    macd          DOUBLE,
    signal_line   DOUBLE,
    bb_middle     DOUBLE,
    bb_upper      DOUBLE,
    bb_lower      DOUBLE,
    CONSTRAINT fk_indicator_price FOREIGN KEY (price_id) REFERENCES price_history(price_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Table 4: news_sentiment
-- One-to-one with price_history. Each trading day in this
-- dataset carries one headline + sentiment scores.
-- ------------------------------------------------------------
CREATE TABLE news_sentiment (
    sentiment_id     INT AUTO_INCREMENT PRIMARY KEY,
    price_id         INT NOT NULL UNIQUE,
    headline         TEXT NOT NULL,
    sentiment_score  DOUBLE NOT NULL, -- compound score, typically between -1 and 1
    sentiment_label  VARCHAR(20),     -- 'positive', 'negative', or 'neutral'
    CONSTRAINT fk_sentiment_price FOREIGN KEY (price_id) REFERENCES price_history(price_id)
        ON DELETE CASCADE
);
