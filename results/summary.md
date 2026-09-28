# Results

Model history: 1990-01-02 to 2026-09-25 (9251 trading days). Evaluation and backtests: 2020-01-02 to 2026-09-25 (1692 trading days).

## Volatility risk premium

|  | value |
|---|---|
| mean_implied_vol | 0.208 |
| mean_realized_vol | 0.169 |
| mean_spread_vol_pts | 3.828 |
| share_positive | 0.849 |
| worst_spread_vol_pts | -71.963 |

## Forecast evaluation (21-day realized variance, out-of-sample)

| model | rmse_vol_pts | mse_variance | qlike | bias_vol_pts | mz_intercept | mz_slope | mz_r2 |
|---|---|---|---|---|---|---|---|
| Implied (VIX^2) | 10.212 | 7.55e-03 | 0.444 | 3.828 | 0.001 | 0.835 | 0.191 |
| HAR | 9.997 | 8.81e-03 | 0.454 | 1.088 | 0.020 | 0.540 | 0.148 |
| HAR-X (HAR + VIX) | 9.586 | 7.97e-03 | 0.477 | 0.945 | 0.016 | 0.659 | 0.180 |
| GARCH(1,1)-t | 10.726 | 1.04e-02 | 0.485 | 1.077 | 0.024 | 0.410 | 0.125 |

## Strategies

| strategy | ann_return | ann_vol | sharpe | max_drawdown | worst_month | skew | cvar_99 | months_traded | psr_vs_0 | deflated_sharpe |
|---|---|---|---|---|---|---|---|---|---|---|
| Short straddle, delta-hedged | 3.9% | 5.6% | 0.70 | -13.6% | -8.3% | -3.79 | 2.2% | 80 | 0.95 | 0.69 |
| Short straddle, unhedged | 0.0% | 13.1% | 0.00 | -24.2% | -9.0% | -1.18 | 4.1% | 80 | 0.50 | 0.10 |
| VRP filter > 0 vol pts | 5.0% | 5.1% | 0.97 | -6.5% | -3.0% | -3.86 | 2.0% | 78 | 0.99 | 0.86 |
| VRP filter > 2 vol pts | 4.5% | 5.0% | 0.89 | -6.5% | -3.0% | -4.06 | 2.0% | 68 | 0.98 | 0.82 |
| VRP filter > 4 vol pts | 3.1% | 3.2% | 0.98 | -4.6% | -1.2% | -7.22 | 1.2% | 19 | 0.98 | 0.84 |

## Sensitivity (delta-hedged short straddle)

| scenario | ann_return | sharpe | max_drawdown | worst_month |
|---|---|---|---|---|
| Base case (ATM vol = VIX - 2 pts) | 3.9% | 0.70 | -13.6% | -8.3% |
| No transaction costs | 5.0% | 0.90 | -13.1% | -8.2% |
| Option half-spread 0.5 vol pt | 3.2% | 0.58 | -13.9% | -8.4% |
| Option half-spread 1.0 vol pt | 1.9% | 0.33 | -14.4% | -8.5% |
| ATM vol = VIX (no skew adjustment) | 9.2% | 1.65 | -12.8% | -8.3% |
| ATM vol = VIX - 3 pts | 1.3% | 0.23 | -14.5% | -8.3% |
| ATM vol = VIX - 4 pts | -1.3% | -0.23 | -17.5% | -8.3% |
| Half notional | 2.0% | 0.70 | -6.8% | -4.1% |

## Stress episodes (cumulative return over the window)

| episode | spx_return | vix_peak | Short straddle, delta-hedged | Short straddle, unhedged | VRP filter > 0 vol pts | VRP filter > 2 vol pts | VRP filter > 4 vol pts |
|---|---|---|---|---|---|---|---|
| Covid crash 2020 | -14.0% | 82.7 | -11.1% | -16.2% | -4.0% | -4.0% | 0.0% |
| Tech selloff Sep 2020 | -8.7% | 40.3 | -0.1% | 3.7% | -0.1% | -0.1% | -0.1% |
| Retail squeeze Jan 2021 | 0.8% | 37.2 | 0.5% | 2.5% | 0.5% | -0.7% | -0.7% |
| Omicron Nov-Dec 2021 | -2.5% | 31.1 | 0.5% | 3.9% | 0.5% | 0.5% | 1.8% |
| Rate shock 2022 | -19.3% | 36.5 | -3.2% | -2.7% | -3.2% | -3.2% | 2.5% |
| Regional banks Mar 2023 | 2.9% | 26.5 | 0.6% | 2.4% | 0.6% | 0.6% | 0.0% |
| Yield spike Oct 2023 | -5.8% | 21.7 | -0.2% | -1.2% | -0.2% | -0.2% | 0.0% |
| Yen carry unwind Aug 2024 | 0.6% | 38.6 | 1.4% | -3.4% | 1.4% | 1.4% | 0.0% |
| Tariff shock Apr 2025 | -1.1% | 52.3 | -3.0% | -9.0% | -3.0% | -3.0% | 1.1% |
| Selloff Mar 2026 | -5.1% | 31.0 | 0.8% | 0.7% | 0.8% | 0.4% | 0.4% |
