import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import StraddleConfig, backtest_short_straddle, vrp_signal
from .data import load_market_data
from .metrics import (deflated_sharpe_ratio, performance_summary, probabilistic_sharpe_ratio,
                      sharpe_per_period, stress_table)
from .plots import plot_attribution, plot_equity, plot_implied_vs_realized, plot_return_distribution
from .report import markdown_table
from .volatility import (evaluate_forecasts, forward_realized_variance, log_returns, walk_forward_garch,
                         walk_forward_har)

THRESHOLDS = (0.0, 2.0, 4.0)
PCT = "{:.1%}"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Volatility risk premium study on the S&P 500.")
    parser.add_argument("--source", choices=["yahoo", "csv"], default="yahoo")
    parser.add_argument("--start", default="1990-01-01",
                        help="first date of the history used to train the forecasting models")
    parser.add_argument("--eval-start", default="2020-01-01",
                        help="first date of the out-of-sample window used for evaluation and backtests")
    parser.add_argument("--end", default=None)
    parser.add_argument("--spx-csv")
    parser.add_argument("--vix-csv")
    parser.add_argument("--refresh", action="store_true", help="download the data again")
    parser.add_argument("--skip-garch", action="store_true", help="skip the GARCH forecasts (much faster)")
    parser.add_argument("--out", default="results")
    return parser.parse_args(argv)


def run_forecasts(returns, implied_var, realized_var, eval_start, skip_garch):
    har, _ = walk_forward_har(returns)
    har_x, har_x_coefs = walk_forward_har(returns, implied_variance=implied_var)
    forecasts = {"HAR": har, "HAR-X (HAR + VIX)": har_x, "Implied (VIX^2)": implied_var.reindex(returns.index)}
    if not skip_garch:
        forecasts["GARCH(1,1)-t"] = walk_forward_garch(returns)
    window = {name: f.loc[eval_start:] for name, f in forecasts.items()}
    evaluation = evaluate_forecasts(window, realized_var.loc[eval_start:])
    evaluation.index.name = "model"
    return har_x, har_x_coefs.loc[eval_start:], evaluation


def volatility_premium(vix, realized_var):
    spread = (vix / 100 - np.sqrt(realized_var)).dropna()
    return pd.Series({
        "mean_implied_vol": (vix / 100).loc[spread.index].mean(),
        "mean_realized_vol": np.sqrt(realized_var).loc[spread.index].mean(),
        "mean_spread_vol_pts": 100 * spread.mean(),
        "share_positive": (spread > 0).mean(),
        "worst_spread_vol_pts": 100 * spread.min(),
    })


def run_strategies(spx, vix, har_x, base):
    runs = {"Short straddle, delta-hedged": backtest_short_straddle(spx, vix, config=base),
            "Short straddle, unhedged": backtest_short_straddle(spx, vix, config=base.with_(delta_hedge=False))}
    for k in THRESHOLDS:
        runs[f"VRP filter > {k:.0f} vol pts"] = backtest_short_straddle(spx, vix, vrp_signal(vix, har_x, k), base)
    return runs


def summarize_strategies(runs):
    returns = {name: daily["return"] for name, (daily, _) in runs.items()}
    trial_sharpes = [sharpe_per_period(r) for r in returns.values()]
    summary = pd.DataFrame({name: performance_summary(r) for name, r in returns.items()}).T
    summary["months_traded"] = [len(trades) for _, trades in runs.values()]
    summary["psr_vs_0"] = [probabilistic_sharpe_ratio(r) for r in returns.values()]
    summary["deflated_sharpe"] = [deflated_sharpe_ratio(r, trial_sharpes) for r in returns.values()]
    summary.index.name = "strategy"
    return returns, summary


def sensitivity_table(spx, vix, base):
    scenarios = {
        "Base case (ATM vol = VIX - 2 pts)": base,
        "No transaction costs": base.with_(option_half_spread_vol=0.0, hedge_cost_bps=0.0),
        "Option half-spread 0.5 vol pt": base.with_(option_half_spread_vol=0.5),
        "Option half-spread 1.0 vol pt": base.with_(option_half_spread_vol=1.0),
        "ATM vol = VIX (no skew adjustment)": base.with_(iv_shift=0.0),
        "ATM vol = VIX - 3 pts": base.with_(iv_shift=-3.0),
        "ATM vol = VIX - 4 pts": base.with_(iv_shift=-4.0),
        "Half notional": base.with_(notional=0.5),
    }
    rows = {}
    for label, config in scenarios.items():
        daily, _ = backtest_short_straddle(spx, vix, config=config)
        rows[label] = performance_summary(daily["return"])[["ann_return", "sharpe", "max_drawdown", "worst_month"]]
    table = pd.DataFrame(rows).T
    table.index.name = "scenario"
    return table


def build_report(spx, sample, vrp_stats, forecast_eval, summary, sensitivity, stress):
    columns = ["ann_return", "ann_vol", "sharpe", "max_drawdown", "worst_month", "skew", "cvar_99",
               "months_traded", "psr_vs_0", "deflated_sharpe"]
    strategy_formats = {"ann_return": PCT, "ann_vol": PCT, "sharpe": "{:.2f}", "max_drawdown": PCT,
                        "worst_month": PCT, "skew": "{:.2f}", "cvar_99": PCT, "months_traded": "{:.0f}",
                        "psr_vs_0": "{:.2f}", "deflated_sharpe": "{:.2f}"}
    stress_formats = {c: PCT for c in stress.columns} | {"vix_peak": "{:.1f}"}
    return "\n".join([
        "# Results",
        "",
        f"Model history: {spx.index[0].date()} to {spx.index[-1].date()} ({len(spx)} trading days). "
        f"Evaluation and backtests: {sample.index[0].date()} to {sample.index[-1].date()} ({len(sample)} trading days).",
        "",
        "## Volatility risk premium",
        "",
        markdown_table(vrp_stats.to_frame("value")),
        "",
        "## Forecast evaluation (21-day realized variance, out-of-sample)",
        "",
        markdown_table(forecast_eval, {"mse_variance": "{:.2e}"}),
        "",
        "## Strategies",
        "",
        markdown_table(summary[columns], strategy_formats),
        "",
        "## Sensitivity (delta-hedged short straddle)",
        "",
        markdown_table(sensitivity, {"ann_return": PCT, "sharpe": "{:.2f}", "max_drawdown": PCT, "worst_month": PCT}),
        "",
        "## Stress episodes (cumulative return over the window)",
        "",
        markdown_table(stress, stress_formats),
        "",
    ])


def main(argv=None):
    args = parse_args(argv)
    out = Path(args.out)
    figures = out / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    eval_start = pd.Timestamp(args.eval_start)

    data = load_market_data(args.source, args.start, args.end, spx_csv=args.spx_csv,
                            vix_csv=args.vix_csv, refresh=args.refresh)
    spx, vix = data["spx"], data["vix"]
    returns = log_returns(spx)
    realized_var = forward_realized_variance(returns)
    implied_var = (vix / 100) ** 2

    har_x, har_x_coefs, forecast_eval = run_forecasts(returns, implied_var, realized_var, eval_start, args.skip_garch)
    forecast_eval.to_csv(out / "forecast_evaluation.csv")
    har_x_coefs.to_csv(out / "har_x_coefficients.csv")

    vrp_stats = volatility_premium(vix.loc[eval_start:], realized_var.loc[eval_start:])

    base = StraddleConfig()
    first = max(eval_start, har_x.first_valid_index())
    sample, vix_sample = spx.loc[first:], vix.loc[first:]

    runs = run_strategies(sample, vix_sample, har_x, base)
    returns_by_strategy, summary = summarize_strategies(runs)
    summary.to_csv(out / "strategy_summary.csv")

    sensitivity = sensitivity_table(sample, vix_sample, base)
    sensitivity.to_csv(out / "sensitivity.csv")

    stress = stress_table(returns_by_strategy, sample, vix_sample)
    stress.index.name = "episode"
    stress.to_csv(out / "stress_episodes.csv")

    main_daily, main_trades = runs["Short straddle, delta-hedged"]
    main_trades.to_csv(out / "trades_delta_hedged.csv", index=False)

    plot_implied_vs_realized(vix_sample, np.sqrt(realized_var).loc[first:], figures / "implied_vs_realized.png")
    plot_equity({k: v for k, v in returns_by_strategy.items() if k != "Short straddle, unhedged"},
                figures / "equity_curves.png")
    plot_attribution(main_daily, base.capital, figures / "pnl_attribution.png")
    plot_return_distribution(main_daily["return"], figures / "return_distribution.png")

    report = build_report(spx, sample, vrp_stats, forecast_eval, summary, sensitivity, stress)
    (out / "summary.md").write_text(report, encoding="utf-8")
    print(report)
