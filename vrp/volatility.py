import numpy as np
import pandas as pd

TRADING_DAYS = 252


def log_returns(prices):
    return np.log(prices).diff().dropna()


def realized_vol(returns, window=21):
    return np.sqrt(TRADING_DAYS * returns.pow(2).rolling(window).mean())


def forward_realized_variance(returns, horizon=21):
    squared = returns.pow(2)
    forward_mean = squared[::-1].rolling(horizon).mean()[::-1].shift(-1)
    return TRADING_DAYS * forward_mean


def har_features(returns):
    rv = TRADING_DAYS * returns.pow(2)
    return pd.DataFrame({
        "rv_d": rv,
        "rv_w": rv.rolling(5).mean(),
        "rv_m": rv.rolling(22).mean(),
    })


def _design(frame):
    return np.column_stack([np.ones(len(frame)), frame.to_numpy()])


def walk_forward_har(returns, implied_variance=None, horizon=21, min_train=504, refit_every=21):
    features = har_features(returns)
    if implied_variance is not None:
        features["iv"] = implied_variance.reindex(features.index)
    features = features.dropna()
    target = forward_realized_variance(returns, horizon).reindex(features.index)

    forecast = pd.Series(np.nan, index=features.index)
    coefficients = []
    for start in range(min_train + horizon, len(features), refit_every):
        train_x = features.iloc[: start - horizon]
        train_y = target.iloc[: start - horizon]
        mask = train_y.notna().to_numpy()
        beta, *_ = np.linalg.lstsq(_design(train_x[mask]), train_y[mask].to_numpy(), rcond=None)
        block = features.iloc[start : start + refit_every]
        forecast.iloc[start : start + refit_every] = _design(block) @ beta
        coefficients.append(pd.Series(beta, index=["const", *features.columns], name=features.index[start]))

    return forecast.clip(lower=0.05**2), pd.DataFrame(coefficients)


def walk_forward_garch(returns, horizon=21, min_train=1000, refit_every=63):
    from arch import arch_model

    scaled = 100 * returns
    forecast = pd.Series(np.nan, index=returns.index)
    for start in range(min_train, len(scaled), refit_every):
        stop = min(start + refit_every, len(scaled))
        fitted = arch_model(scaled.iloc[:start], mean="Zero", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
        fixed = arch_model(scaled.iloc[:stop], mean="Zero", vol="GARCH", p=1, q=1, dist="t").fix(fitted.params)
        variance = fixed.forecast(horizon=horizon, start=start, reindex=False).variance
        forecast.loc[variance.index] = variance.mean(axis=1).to_numpy() * TRADING_DAYS / 1e4
    return forecast


def evaluate_forecasts(forecasts, realized_variance):
    aligned = pd.concat({**forecasts, "realized": realized_variance}, axis=1, sort=True).dropna()
    y = aligned.pop("realized")
    rows = {}
    for name, f in aligned.items():
        error = y - f
        ratio = y / f
        slope, intercept = np.polyfit(f, y, 1)
        rows[name] = {
            "rmse_vol_pts": 100 * np.sqrt((np.sqrt(y) - np.sqrt(f)).pow(2).mean()),
            "mse_variance": error.pow(2).mean(),
            "qlike": (ratio - np.log(ratio) - 1).mean(),
            "bias_vol_pts": 100 * (np.sqrt(f) - np.sqrt(y)).mean(),
            "mz_intercept": intercept,
            "mz_slope": slope,
            "mz_r2": np.corrcoef(f, y)[0, 1] ** 2,
        }
    table = pd.DataFrame(rows).T
    table.attrs["start"], table.attrs["end"], table.attrs["n"] = y.index[0], y.index[-1], len(y)
    return table.sort_values("qlike")
