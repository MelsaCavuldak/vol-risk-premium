from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from .pricing import straddle_delta, straddle_price, straddle_vega
from .volatility import TRADING_DAYS


@dataclass(frozen=True)
class StraddleConfig:
    capital: float = 1_000_000.0
    notional: float = 1.0
    maturity_days: int = 21
    rate: float = 0.0
    iv_shift: float = -2.0
    option_half_spread_vol: float = 0.25
    hedge_cost_bps: float = 1.0
    delta_hedge: bool = True

    def with_(self, **changes):
        return replace(self, **changes)


def backtest_short_straddle(spx, vix, signal=None, config=StraddleConfig()):
    dates = spx.index
    spot = spx.to_numpy(float)
    vol = np.maximum((vix.reindex(dates).to_numpy(float) + config.iv_shift) / 100.0, 0.01)
    trade_flags = None if signal is None else signal.reindex(dates).fillna(False).to_numpy(bool)
    n = len(spot)

    option_pnl = np.zeros(n)
    hedge_pnl = np.zeros(n)
    vega_pnl = np.zeros(n)
    costs = np.zeros(n)
    exposure = np.zeros(n)
    trades = []

    t = 0
    while t + config.maturity_days <= n - 1:
        expiry = t + config.maturity_days
        if trade_flags is not None and not trade_flags[t]:
            t = expiry
            continue

        strike = spot[t]
        quantity = config.notional * config.capital / spot[t]
        tau = config.maturity_days / TRADING_DAYS
        value = straddle_price(spot[t], strike, tau, vol[t], config.rate)
        vega = straddle_vega(spot[t], strike, tau, vol[t], config.rate)
        hedge = quantity * straddle_delta(spot[t], strike, tau, vol[t], config.rate) if config.delta_hedge else 0.0

        entry_cost = quantity * vega * config.option_half_spread_vol / 100.0 + abs(hedge) * spot[t] * config.hedge_cost_bps / 1e4
        costs[t] += entry_cost
        trade_costs = entry_cost
        premium = quantity * value

        for k in range(t + 1, expiry + 1):
            tau = (config.maturity_days - (k - t)) / TRADING_DAYS
            new_value = straddle_price(spot[k], strike, tau, vol[k], config.rate)
            option_pnl[k] = -quantity * (new_value - value)
            hedge_pnl[k] = hedge * (spot[k] - spot[k - 1])
            vega_pnl[k] = -quantity * vega * (vol[k] - vol[k - 1])
            exposure[k] = 1.0

            if k < expiry:
                new_hedge = quantity * straddle_delta(spot[k], strike, tau, vol[k], config.rate) if config.delta_hedge else 0.0
                vega = straddle_vega(spot[k], strike, tau, vol[k], config.rate)
            else:
                new_hedge = 0.0
                vega = 0.0
            rebalance_cost = abs(new_hedge - hedge) * spot[k] * config.hedge_cost_bps / 1e4
            costs[k] += rebalance_cost
            trade_costs += rebalance_cost
            hedge, value = new_hedge, new_value

        trade_pnl = option_pnl[t + 1 : expiry + 1].sum() + hedge_pnl[t + 1 : expiry + 1].sum() - trade_costs
        trades.append({
            "entry": dates[t],
            "expiry": dates[expiry],
            "strike": strike,
            "implied_vol": vol[t],
            "realized_vol": np.sqrt(TRADING_DAYS * np.mean(np.diff(np.log(spot[t : expiry + 1])) ** 2)),
            "premium": premium,
            "pnl": trade_pnl,
            "return_on_capital": trade_pnl / config.capital,
        })
        t = expiry

    daily = pd.DataFrame({
        "option_pnl": option_pnl,
        "hedge_pnl": hedge_pnl,
        "costs": costs,
        "vega_pnl": vega_pnl,
        "in_position": exposure,
    }, index=dates)
    daily["pnl"] = daily["option_pnl"] + daily["hedge_pnl"] - daily["costs"]
    daily["gamma_theta_pnl"] = daily["option_pnl"] + daily["hedge_pnl"] - daily["vega_pnl"]
    daily["return"] = daily["pnl"] / config.capital
    daily["equity"] = config.capital + daily["pnl"].cumsum()
    return daily, pd.DataFrame(trades)


def vrp_signal(vix, variance_forecast, threshold_vol_pts=0.0):
    spread = vix / 100.0 - np.sqrt(variance_forecast.reindex(vix.index))
    return (spread > threshold_vol_pts / 100.0) & spread.notna()
