import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

EULER_GAMMA = 0.5772156649015329

STRESS_EPISODES = {
    "Covid crash 2020": ("2020-02-19", "2020-04-30"),
    "Tech selloff Sep 2020": ("2020-09-02", "2020-10-30"),
    "Retail squeeze Jan 2021": ("2021-01-25", "2021-02-05"),
    "Omicron Nov-Dec 2021": ("2021-11-22", "2021-12-20"),
    "Rate shock 2022": ("2022-01-01", "2022-10-31"),
    "Regional banks Mar 2023": ("2023-03-08", "2023-03-31"),
    "Yield spike Oct 2023": ("2023-09-15", "2023-10-31"),
    "Yen carry unwind Aug 2024": ("2024-07-31", "2024-08-16"),
    "Tariff shock Apr 2025": ("2025-04-01", "2025-04-30"),
    "Selloff Mar 2026": ("2026-03-02", "2026-03-31"),
}


def drawdown(returns):
    equity = returns.cumsum()
    return equity - equity.cummax()


def performance_summary(returns, periods=252):
    r = returns.dropna()
    ann_return = r.mean() * periods
    ann_vol = r.std(ddof=1) * np.sqrt(periods)
    downside = np.sqrt(r.clip(upper=0).pow(2).mean()) * np.sqrt(periods)
    max_dd = drawdown(r).min()
    q05, q01 = r.quantile(0.05), r.quantile(0.01)
    monthly = r.resample("ME").sum()
    return pd.Series({
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": ann_return / ann_vol if ann_vol > 0 else np.nan,
        "sortino": ann_return / downside if downside > 0 else np.nan,
        "max_drawdown": max_dd,
        "calmar": ann_return / abs(max_dd) if max_dd < 0 else np.nan,
        "skew": skew(r),
        "excess_kurtosis": kurtosis(r),
        "var_95": -q05,
        "cvar_95": -r[r <= q05].mean(),
        "var_99": -q01,
        "cvar_99": -r[r <= q01].mean(),
        "worst_day": r.min(),
        "worst_month": monthly.min(),
        "positive_months": (monthly > 0).mean(),
    })


def sharpe_per_period(returns):
    r = returns.dropna()
    return r.mean() / r.std(ddof=1)


def probabilistic_sharpe_ratio(returns, benchmark_sr=0.0):
    r = returns.dropna()
    sr = sharpe_per_period(r)
    denominator = np.sqrt(1 - skew(r) * sr + (kurtosis(r, fisher=False) - 1) / 4 * sr**2)
    return norm.cdf((sr - benchmark_sr) * np.sqrt(len(r) - 1) / denominator)


def expected_max_sharpe(trial_sharpes):
    trial_sharpes = np.asarray(trial_sharpes, float)
    n = len(trial_sharpes)
    spread = np.sqrt(np.var(trial_sharpes, ddof=1))
    return spread * ((1 - EULER_GAMMA) * norm.ppf(1 - 1 / n) + EULER_GAMMA * norm.ppf(1 - 1 / (n * np.e)))


def deflated_sharpe_ratio(returns, trial_sharpes):
    return probabilistic_sharpe_ratio(returns, expected_max_sharpe(trial_sharpes))


def stress_table(strategy_returns, spx, vix, episodes=STRESS_EPISODES):
    rows = {}
    for name, (start, end) in episodes.items():
        window = spx.loc[start:end]
        if len(window) < 5:
            continue
        row = {
            "spx_return": window.iloc[-1] / window.iloc[0] - 1,
            "vix_peak": vix.loc[start:end].max(),
        }
        for label, returns in strategy_returns.items():
            row[label] = returns.loc[start:end].sum()
        rows[name] = row
    return pd.DataFrame(rows).T
