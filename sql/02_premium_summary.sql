-- Headline figures of the volatility risk premium from $start onwards.
-- Volatilities are in decimals (0.208 is 20.8%), gaps in volatility points.
WITH gap AS (
    SELECT
        vix / 100 AS implied_vol,
        SQRT(forward_variance) AS realized_vol,
        vix - 100 * SQRT(forward_variance) AS gap_points
    FROM daily
    WHERE forward_variance IS NOT NULL
      AND day >= CAST($start AS DATE)
)
SELECT
    AVG(implied_vol) AS mean_implied_vol,
    AVG(realized_vol) AS mean_realized_vol,
    AVG(gap_points) AS mean_spread_vol_pts,
    AVG((gap_points > 0)::INT) AS share_positive,
    MIN(gap_points) AS worst_spread_vol_pts
FROM gap;
