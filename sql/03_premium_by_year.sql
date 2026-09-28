-- The premium year by year, from $start onwards.
SELECT
    YEAR(day) AS year,
    AVG(vix) AS average_vix,
    AVG(100 * SQRT(forward_variance)) AS average_realized_vol,
    AVG(vix - 100 * SQRT(forward_variance)) AS gap_vol_points,
    AVG((vix - 100 * SQRT(forward_variance) > 0)::INT) AS share_of_days_vix_above,
    MIN(vix - 100 * SQRT(forward_variance)) AS worst_gap_vol_points
FROM daily
WHERE forward_variance IS NOT NULL
  AND day >= CAST($start AS DATE)
GROUP BY YEAR(day)
ORDER BY year;
