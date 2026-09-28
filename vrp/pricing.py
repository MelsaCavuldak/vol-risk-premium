import numpy as np
from scipy.stats import norm


def _d1(spot, strike, tau, vol, rate=0.0, div=0.0):
    return (np.log(spot / strike) + (rate - div + 0.5 * vol**2) * tau) / (vol * np.sqrt(tau))


def call_price(spot, strike, tau, vol, rate=0.0, div=0.0):
    if tau <= 0:
        return max(spot - strike, 0.0)
    d1 = _d1(spot, strike, tau, vol, rate, div)
    d2 = d1 - vol * np.sqrt(tau)
    return spot * np.exp(-div * tau) * norm.cdf(d1) - strike * np.exp(-rate * tau) * norm.cdf(d2)


def put_price(spot, strike, tau, vol, rate=0.0, div=0.0):
    if tau <= 0:
        return max(strike - spot, 0.0)
    d1 = _d1(spot, strike, tau, vol, rate, div)
    d2 = d1 - vol * np.sqrt(tau)
    return strike * np.exp(-rate * tau) * norm.cdf(-d2) - spot * np.exp(-div * tau) * norm.cdf(-d1)


def straddle_price(spot, strike, tau, vol, rate=0.0, div=0.0):
    return call_price(spot, strike, tau, vol, rate, div) + put_price(spot, strike, tau, vol, rate, div)


def straddle_delta(spot, strike, tau, vol, rate=0.0, div=0.0):
    if tau <= 0:
        return float(np.sign(spot - strike))
    d1 = _d1(spot, strike, tau, vol, rate, div)
    return np.exp(-div * tau) * (2 * norm.cdf(d1) - 1)


def straddle_gamma(spot, strike, tau, vol, rate=0.0, div=0.0):
    if tau <= 0:
        return 0.0
    d1 = _d1(spot, strike, tau, vol, rate, div)
    return 2 * np.exp(-div * tau) * norm.pdf(d1) / (spot * vol * np.sqrt(tau))


def straddle_vega(spot, strike, tau, vol, rate=0.0, div=0.0):
    if tau <= 0:
        return 0.0
    d1 = _d1(spot, strike, tau, vol, rate, div)
    return 2 * spot * np.exp(-div * tau) * norm.pdf(d1) * np.sqrt(tau)
