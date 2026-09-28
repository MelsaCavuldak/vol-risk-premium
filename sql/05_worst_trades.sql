-- The five worst trades, with the volatility charged at entry and the volatility that followed.
SELECT
    entry,
    expiry,
    implied_vol,
    realized_vol,
    100 * return_on_capital AS pnl_pct
FROM trades
ORDER BY return_on_capital
LIMIT 5;
