

CREATE TABLE IF NOT EXISTS stocks (
    stock_id      INT AUTO_INCREMENT PRIMARY KEY,
    symbol        VARCHAR(20) NOT NULL UNIQUE,
    company_name  VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS price_history (
    price_id      INT AUTO_INCREMENT PRIMARY KEY,
    stock_id      INT NOT NULL,
    trade_date    DATE NOT NULL,
    open_price    DOUBLE,
    high_price    DOUBLE,
    low_price     DOUBLE,
    close_price   DOUBLE,
    volume        DOUBLE,
    target        INT,
    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
    UNIQUE KEY uniq_stock_date (stock_id, trade_date)
);

CREATE TABLE IF NOT EXISTS technical_indicators (
    indicator_id  INT AUTO_INCREMENT PRIMARY KEY,
    price_id      INT NOT NULL,
    sma_10        DOUBLE,
    sma_20        DOUBLE,
    ema_10        DOUBLE,
    rsi           DOUBLE,
    macd          DOUBLE,
    signal_line   DOUBLE,
    bb_middle     DOUBLE,
    bb_upper      DOUBLE,
    bb_lower      DOUBLE,
    FOREIGN KEY (price_id) REFERENCES price_history(price_id)
);

CREATE TABLE IF NOT EXISTS news_sentiment (
    sentiment_id     INT AUTO_INCREMENT PRIMARY KEY,
    price_id         INT NOT NULL,
    headline         VARCHAR(500),
    sentiment_score  DOUBLE,
    sentiment_label  VARCHAR(20),
    FOREIGN KEY (price_id) REFERENCES price_history(price_id)
);


CREATE INDEX idx_price_history_date ON price_history(trade_date);
CREATE INDEX idx_technical_indicators_price ON technical_indicators(price_id);
CREATE INDEX idx_news_sentiment_price ON news_sentiment(price_id);
