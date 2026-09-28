import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from scipy.stats import norm

from .metrics import drawdown

PALETTE = ["#1f4e79", "#c0504d", "#4f8f4f", "#8064a2", "#d08a2e", "#4bacc6"]


def _style(ax, title):
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    ax.grid(alpha=0.25)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def plot_implied_vs_realized(vix, forward_realized_vol, path):
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    implied = vix / 100
    top.plot(implied.index, implied, color=PALETTE[0], lw=0.8, label="VIX (30-day implied)")
    top.plot(forward_realized_vol.index, forward_realized_vol, color=PALETTE[1], lw=0.8, label="Next 21-day realized")
    top.legend(frameon=False)
    top.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    _style(top, "S&P 500: implied vs subsequently realized volatility")

    spread = (implied - forward_realized_vol).dropna()
    bottom.fill_between(spread.index, 0, spread, where=spread >= 0, color=PALETTE[2], alpha=0.6, lw=0)
    bottom.fill_between(spread.index, 0, spread, where=spread < 0, color=PALETTE[1], alpha=0.6, lw=0)
    bottom.axhline(0, color="black", lw=0.6)
    bottom.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    _style(bottom, f"Implied minus realized (positive {100 * (spread > 0).mean():.0f}% of days)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_equity(returns_by_strategy, path):
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    for color, (label, returns) in zip(PALETTE, returns_by_strategy.items()):
        top.plot(returns.index, returns.cumsum(), color=color, lw=1.0, label=label)
        bottom.plot(returns.index, drawdown(returns), color=color, lw=0.8)
    top.axhline(0, color="black", lw=0.6)
    top.legend(frameon=False, fontsize=9)
    top.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    bottom.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    _style(top, "Cumulative P&L (% of capital, non-compounded)")
    _style(bottom, "Drawdown")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_attribution(daily, capital, path):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    parts = {
        "Gamma / theta": daily["gamma_theta_pnl"],
        "Vega (implied vol changes)": daily["vega_pnl"],
        "Transaction costs": -daily["costs"],
        "Total": daily["pnl"],
    }
    for color, (label, pnl) in zip([PALETTE[2], PALETTE[1], PALETTE[4], PALETTE[0]], parts.items()):
        ax.plot(pnl.index, pnl.cumsum() / capital, color=color, lw=1.6 if label == "Total" else 1.0, label=label)
    ax.axhline(0, color="black", lw=0.6)
    ax.legend(frameon=False, fontsize=9)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    _style(ax, "P&L attribution of the delta-hedged short straddle")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_return_distribution(returns, path):
    r = returns[returns != 0].dropna()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    bins = np.linspace(r.min(), r.max(), 80)
    width = bins[1] - bins[0]
    ax.hist(r, bins=bins, color=PALETTE[0], alpha=0.7, label="Daily returns (days in position)")
    grid = np.linspace(r.min(), r.max(), 400)
    expected = len(r) * width * norm.pdf(grid, r.mean(), r.std())
    ax.plot(grid, expected, color=PALETTE[1], lw=1.2, label="Normal with same mean and vol")
    ax.set_yscale("log")
    ax.set_ylim(0.5, expected.max() * 3)
    ax.set_ylabel("Number of days")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    _style(ax, "Distribution of daily returns (log scale)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
