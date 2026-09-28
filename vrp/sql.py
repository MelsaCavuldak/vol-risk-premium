"""Run the SQL queries of the ``sql/`` folder on an in-memory DuckDB database.

DuckDB runs inside the Python process, so there is no server to set up. The queries are plain text files, one per
question, and they are kept apart from the code so that they can be read on their own.
"""

from pathlib import Path

import duckdb
import pandas as pd

from .metrics import STRESS_EPISODES

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def read_query(name):
    return (SQL_DIR / f"{name}.sql").read_text(encoding="utf-8")


def run(connection, name, **parameters):
    """Execute one query file and return its result as a DataFrame (None for statements without a result)."""
    cursor = connection.execute(read_query(name), parameters) if parameters else connection.execute(read_query(name))
    return cursor.df() if cursor.description else None


def connect(spx, vix, trades=None, episodes=STRESS_EPISODES):
    """A database holding the market data, the trades of the backtest and the stress windows.

    ``market`` has one row per trading day, ``trades`` one row per option trade and ``episodes`` one row per stress
    window. The ``daily`` view with the forward realized variance is created on top of ``market``.
    """
    connection = duckdb.connect()
    market = pd.DataFrame({"day": pd.to_datetime(spx.index), "spx": spx.to_numpy(float), "vix": vix.reindex(spx.index).to_numpy(float)})
    connection.register("market", market)
    if trades is not None:
        connection.register("trades", trades.assign(entry=pd.to_datetime(trades["entry"]), expiry=pd.to_datetime(trades["expiry"])))
    windows = pd.DataFrame(
        [(name, pd.Timestamp(start), pd.Timestamp(end)) for name, (start, end) in episodes.items()],
        columns=["episode", "start_date", "end_date"],
    )
    connection.register("episodes", windows)
    run(connection, "01_daily")
    return connection
