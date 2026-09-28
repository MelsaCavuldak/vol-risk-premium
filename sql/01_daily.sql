-- Daily log returns and the forward 21-day realized variance, annualized.
--
--   RV(t, t+21) = 252 / 21 * sum_{i=1..21} r(t+i)^2
--
-- The frame looks at the 21 rows after the current one. The count guard leaves the last
-- 21 days empty, exactly as the Python version does, instead of averaging fewer returns.
CREATE OR REPLACE VIEW daily AS
WITH returns AS (
    SELECT day, spx, vix, LN(spx / LAG(spx) OVER (ORDER BY day)) AS r
    FROM market
),
squared AS (
    SELECT day, spx, vix, r, r * r AS r2
    FROM returns
    WHERE r IS NOT NULL
)
SELECT
    day,
    spx,
    vix,
    r,
    CASE WHEN COUNT(r2) OVER next_21 = 21 THEN 252 * AVG(r2) OVER next_21 END AS forward_variance
FROM squared
WINDOW next_21 AS (ORDER BY day ROWS BETWEEN 1 FOLLOWING AND 21 FOLLOWING);
