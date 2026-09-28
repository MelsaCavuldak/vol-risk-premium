import numpy as np
import pandas as pd
import pytest

from vrp.volatility import forward_realized_variance, walk_forward_har


def simulated_returns(n=2500, seed=7):
    rng = np.random.default_rng(seed)
    variance = np.empty(n)
    returns = np.empty(n)
    variance[0] = 0.01**2
    for t in range(n):
        if t > 0:
            variance[t] = 2e-6 + 0.08 * returns[t - 1] ** 2 + 0.9 * variance[t - 1]
        returns[t] = np.sqrt(variance[t]) * rng.standard_normal()
    return pd.Series(returns, index=pd.bdate_range("2000-01-03", periods=n))


def test_forward_realized_variance_uses_next_days_only():
    returns = pd.Series(np.arange(1, 11, dtype=float), index=pd.bdate_range("2020-01-01", periods=10))
    forward = forward_realized_variance(returns, horizon=3)
    assert forward.iloc[0] == pytest.approx(252 * (4 + 9 + 16) / 3)
    assert forward.iloc[-3:].isna().all()


def test_har_forecasts_do_not_look_ahead():
    returns = simulated_returns()
    baseline, _ = walk_forward_har(returns)
    cutoff = 1800
    shocked = returns.copy()
    shocked.iloc[cutoff:] *= 5
    perturbed, _ = walk_forward_har(shocked)
    common = baseline.index[baseline.index < returns.index[cutoff]]
    pd.testing.assert_series_equal(baseline.loc[common], perturbed.loc[common])


def test_har_beats_naive_mean_out_of_sample():
    returns = simulated_returns()
    forecast, _ = walk_forward_har(returns)
    realized = forward_realized_variance(returns)
    frame = pd.concat([forecast.rename("f"), realized.rename("y")], axis=1, sort=True).dropna()
    naive = realized.expanding().mean().shift(21).reindex(frame.index)
    assert ((frame.y - frame.f) ** 2).mean() < ((frame.y - naive) ** 2).mean()
