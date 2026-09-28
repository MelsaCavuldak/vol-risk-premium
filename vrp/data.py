from pathlib import Path

import pandas as pd

TICKERS = {"spx": "^GSPC", "vix": "^VIX"}


def download_yahoo(start):
    import yfinance as yf

    series = []
    for name, ticker in TICKERS.items():
        raw = yf.download(ticker, start=start, auto_adjust=False, progress=False)
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        series.append(close.rename(name))
    data = pd.concat(series, axis=1, sort=True).dropna()
    data.index = pd.to_datetime(data.index).tz_localize(None)
    data.index.name = "date"
    return data


def read_close(path):
    raw = pd.read_csv(path)
    columns = {c.strip().strip('"').lower(): c for c in raw.columns}
    close_col = columns.get("adj close", columns.get("close"))
    series = pd.Series(raw[close_col].astype(float).values, index=pd.to_datetime(raw[columns["date"]]))
    series.index.name = "date"
    return series.sort_index()


def load_csv(spx_path, vix_path):
    data = pd.concat([read_close(spx_path).rename("spx"), read_close(vix_path).rename("vix")], axis=1, sort=True)
    return data.dropna()


def load_market_data(source="yahoo", start="1990-01-01", end=None, cache="data/market.csv",
                     spx_csv=None, vix_csv=None, refresh=False):
    if source == "csv":
        data = load_csv(spx_csv, vix_csv)
    else:
        cache = Path(cache)
        data = None
        if cache.exists() and not refresh:
            data = pd.read_csv(cache, index_col=0, parse_dates=True)
            if data.index[0] > pd.Timestamp(start) + pd.Timedelta(days=10):
                data = None
        if data is None:
            data = download_yahoo(start)
            cache.parent.mkdir(parents=True, exist_ok=True)
            data.to_csv(cache)
    data = data.loc[start:end]
    data = data[(data["spx"] > 0) & (data["vix"] > 0)]
    return data[["spx", "vix"]].astype(float)
