-- The S&P 500 move and the VIX peak inside each stress window.
-- arg_max / arg_min pick the index level on the last and first day of the window.
SELECT
    e.episode,
    arg_max(d.spx, d.day) / arg_min(d.spx, d.day) - 1 AS spx_return,
    MAX(d.vix) AS vix_peak
FROM episodes AS e
JOIN daily AS d ON d.day BETWEEN e.start_date AND e.end_date
GROUP BY e.episode, e.start_date
HAVING COUNT(*) >= 5
ORDER BY e.start_date;
