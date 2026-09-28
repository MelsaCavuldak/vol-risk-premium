import numpy as np
import pandas as pd
import pytest

from vrp.backtest import StraddleConfig, backtest_short_straddle
from vrp.metrics import stress_table
from vrp.pipeline import volatility_premium
from vrp.sql import connect, run
from vrp.volatility import forward_realized_variance, log_returns

DATES = pd.bdate_range("2021-01-04", periods=260)
EPISODES = {"first": ("2021-03-01", "2021-04-30"), "second": ("2021-08-02", "2021-09-30")}


@pytest.fixture(scope="module")
def market():
    rng = np.random.default_rng(11)
    spx = pd.Series(4000.0 * np.exp(np.cumsum(0.01 * rng.standard_normal(len(DATES)))), index=DATES)
    vix = pd.Series(18.0 + 6.0 * np.abs(rng.standard_normal(len(DATES))), index=DATES)
    return spx, vix


@pytest.fixture(scope="module")
def trades(market):
    spx, vix = market
    return backtest_short_straddle(spx, vix, config=StraddleConfig())[1]


@pytest.fixture(scope="module")
def connection(market, trades):
    spx, vix = market
    return connect(spx, vix, trades, EPISODES)


def test_forward_variance_matches_the_python_version(market, connection):
    spx, _ = market
    expected = forward_realized_variance(log_returns(spx))
    result = connection.execute("SELECT day, forward_variance FROM daily ORDER BY day").df().set_index("day")["forward_variance"]
    assert len(result) == len(expected)
    assert result.isna().to_numpy().tolist() == expected.isna().to_numpy().tolist()
    assert result.dropna().to_numpy() == pytest.approx(expected.dropna().to_numpy(), rel=1e-12)


def test_the_last_21_days_have_no_forward_variance(connection):
    empty = connection.execute("SELECT COUNT(*) FROM daily WHERE forward_variance IS NULL").fetchone()[0]
    assert empty == 21


def test_premium_summary_matches_the_python_version(market, connection):
    spx, vix = market
    realized = forward_realized_variance(log_returns(spx))
    expected = volatility_premium(vix.loc["2021-03-01":], realized.loc["2021-03-01":])
    result = run(connection, "02_premium_summary", start="2021-03-01").iloc[0]
    for name in expected.index:
        assert result[name] == pytest.approx(expected[name], rel=1e-12)


def test_premium_by_year_covers_every_year_with_data(connection):
    table = run(connection, "03_premium_by_year", start="2021-01-01")
    assert table["year"].tolist() == [2021]
    assert 0.0 <= table.loc[0, "share_of_days_vix_above"] <= 1.0


def test_trade_summary_matches_pandas(trades, connection):
    result = run(connection, "04_trade_summary").iloc[0]
    returns = trades["return_on_capital"]
    assert result["trades"] == len(trades)
    assert result["win_rate"] == pytest.approx((returns > 0).mean())
    assert result["average_win"] == pytest.approx(returns[returns > 0].mean())
    assert result["average_loss"] == pytest.approx(returns[returns <= 0].mean())
    assert result["worst_trade"] == pytest.approx(returns.min())


def test_worst_trades_are_sorted_from_the_worst(trades, connection):
    result = run(connection, "05_worst_trades")
    assert len(result) == min(5, len(trades))
    assert result["pnl_pct"].is_monotonic_increasing
    assert result.loc[0, "pnl_pct"] == pytest.approx(100 * trades["return_on_capital"].min())


def test_stress_episodes_match_the_python_version(market, connection):
    spx, vix = market
    expected = stress_table({"s": pd.Series(0.0, index=spx.index)}, spx, vix, EPISODES)
    result = run(connection, "06_stress_episodes").set_index("episode")
    assert list(result.index) == list(expected.index)
    assert result["spx_return"].to_numpy() == pytest.approx(expected["spx_return"].to_numpy(), rel=1e-12)
    assert result["vix_peak"].to_numpy() == pytest.approx(expected["vix_peak"].to_numpy(), rel=1e-12)


def test_short_windows_are_left_out(market):
    spx, vix = market
    con = connect(spx, vix, None, {"tiny": ("2021-03-01", "2021-03-03")})
    assert len(run(con, "06_stress_episodes")) == 0
