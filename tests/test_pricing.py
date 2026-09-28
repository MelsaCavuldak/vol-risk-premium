import numpy as np
import pytest

from vrp.pricing import call_price, put_price, straddle_delta, straddle_gamma, straddle_price, straddle_vega

SPOT, STRIKE, TAU, VOL, RATE = 4500.0, 4450.0, 21 / 252, 0.18, 0.03


def test_put_call_parity():
    lhs = call_price(SPOT, STRIKE, TAU, VOL, RATE) - put_price(SPOT, STRIKE, TAU, VOL, RATE)
    assert lhs == pytest.approx(SPOT - STRIKE * np.exp(-RATE * TAU), rel=1e-10)


def test_atm_straddle_approximation():
    price = straddle_price(SPOT, SPOT, TAU, VOL)
    assert price == pytest.approx(0.8 * SPOT * VOL * np.sqrt(TAU), rel=0.01)


def test_greeks_match_finite_differences():
    h = 1e-3 * SPOT
    fd_delta = (straddle_price(SPOT + h, STRIKE, TAU, VOL, RATE) - straddle_price(SPOT - h, STRIKE, TAU, VOL, RATE)) / (2 * h)
    fd_gamma = (straddle_price(SPOT + h, STRIKE, TAU, VOL, RATE) - 2 * straddle_price(SPOT, STRIKE, TAU, VOL, RATE)
                + straddle_price(SPOT - h, STRIKE, TAU, VOL, RATE)) / h**2
    fd_vega = (straddle_price(SPOT, STRIKE, TAU, VOL + 1e-4, RATE) - straddle_price(SPOT, STRIKE, TAU, VOL - 1e-4, RATE)) / 2e-4
    assert straddle_delta(SPOT, STRIKE, TAU, VOL, RATE) == pytest.approx(fd_delta, rel=1e-4)
    assert straddle_gamma(SPOT, STRIKE, TAU, VOL, RATE) == pytest.approx(fd_gamma, rel=1e-3)
    assert straddle_vega(SPOT, STRIKE, TAU, VOL, RATE) == pytest.approx(fd_vega, rel=1e-4)


def test_expiry_payoff():
    assert straddle_price(4600.0, STRIKE, 0.0, VOL) == pytest.approx(150.0)
    assert straddle_price(4300.0, STRIKE, 0.0, VOL) == pytest.approx(150.0)
    assert straddle_delta(4300.0, STRIKE, 0.0, VOL) == -1.0
    assert straddle_vega(4300.0, STRIKE, 0.0, VOL) == 0.0
