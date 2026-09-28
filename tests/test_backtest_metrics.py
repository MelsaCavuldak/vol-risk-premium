import numpy as np
import pandas as pd
import pytest

from vrp.backtest import StraddleConfig, backtest_short_straddle, vrp_signal
from vrp.metrics import (deflated_sharpe_ratio, drawdown, expected_max_sharpe, probabilistic_sharpe_ratio,
                         stress_table)
from vrp.pricing import straddle_price

DATES = pd.bdate_range("2021-01-04", periods=64)


def test_flat_market_keeps_full_premium():
    spx = pd.Series(4000.0, index=DATES)
    vix = pd.Series(20.0, index=DATES)
    config = StraddleConfig(option_half_spread_vol=0.0, hedge_cost_bps=0.0, iv_shift=0.0)
    daily, trades = backtest_short_straddle(spx, vix, config=config)
    premium_per_trade = config.capital / 4000.0 * straddle_price(4000.0, 4000.0, 21 / 252, 0.20)
    assert len(trades) == 3
    assert daily["pnl"].sum() == pytest.approx(3 * premium_per_trade, rel=1e-9)
    assert trades["pnl"].to_numpy() == pytest.approx([premium_per_trade] * 3, rel=1e-9)


def test_costs_reduce_pnl_and_signal_skips_trades():
    rng = np.random.default_rng(0)
    spx = pd.Series(4000.0 * np.exp(np.cumsum(0.01 * rng.standard_normal(len(DATES)))), index=DATES)
    vix = pd.Series(18.0, index=DATES)
    cheap, _ = backtest_short_straddle(spx, vix, config=StraddleConfig(option_half_spread_vol=0.0, hedge_cost_bps=0.0))
    costly, _ = backtest_short_straddle(spx, vix, config=StraddleConfig())
    assert costly["pnl"].sum() < cheap["pnl"].sum()

    signal = vrp_signal(vix, pd.Series(0.25**2, index=DATES))
    skipped, trades = backtest_short_straddle(spx, vix, signal=signal)
    assert trades.empty and skipped["pnl"].abs().sum() == 0


def test_drawdown():
    returns = pd.Series([0.1, -0.05, -0.1, 0.2, -0.3])
    assert drawdown(returns).min() == pytest.approx(-0.3)


def test_sharpe_statistics():
    rng = np.random.default_rng(1)
    good = pd.Series(0.001 + 0.01 * rng.standard_normal(5000))
    noise = pd.Series(0.01 * rng.standard_normal(5000))
    assert probabilistic_sharpe_ratio(good) > 0.99
    assert 0.0 < probabilistic_sharpe_ratio(noise) < 1.0
    trials = [0.02, 0.05, 0.08, 0.1, 0.03]
    assert expected_max_sharpe(trials) > 0
    assert deflated_sharpe_ratio(good, trials) <= probabilistic_sharpe_ratio(good)


def test_trade_pnl_reconciles_with_daily_pnl():
    rng = np.random.default_rng(3)
    dates = pd.bdate_range("2021-01-04", periods=127)
    spx = pd.Series(4000.0 * np.exp(np.cumsum(0.01 * rng.standard_normal(len(dates)))), index=dates)
    vix = pd.Series(20.0, index=dates)
    daily, trades = backtest_short_straddle(spx, vix)
    assert len(trades) == 6
    assert trades["pnl"].sum() == pytest.approx(daily["pnl"].sum(), rel=1e-9)
    assert trades["expiry"].max() <= dates[-1]


def test_no_position_is_opened_without_a_full_maturity_left():
    dates = pd.bdate_range("2021-01-04", periods=30)
    spx = pd.Series(4000.0, index=dates)
    vix = pd.Series(20.0, index=dates)
    daily, trades = backtest_short_straddle(spx, vix)
    assert len(trades) == 1
    assert daily["in_position"].iloc[22:].sum() == 0


def test_stress_table_skips_episodes_outside_the_sample():
    returns = pd.Series(0.001, index=DATES)
    spx = pd.Series(4000.0, index=DATES)
    vix = pd.Series(20.0, index=DATES)
    episodes = {"inside": ("2021-01-11", "2021-02-26"), "outside": ("2015-08-17", "2015-09-30")}
    table = stress_table({"s": returns}, spx, vix, episodes)
    assert list(table.index) == ["inside"]
    assert table.loc["inside", "s"] == pytest.approx(0.001 * len(returns.loc["2021-01-11":"2021-02-26"]))
