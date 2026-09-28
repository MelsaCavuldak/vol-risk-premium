-- How the monthly trades of the delta-hedged strategy turned out, as a share of capital.
SELECT
    COUNT(*) AS trades,
    AVG((return_on_capital > 0)::INT) AS win_rate,
    AVG(return_on_capital) FILTER (WHERE return_on_capital > 0) AS average_win,
    AVG(return_on_capital) FILTER (WHERE return_on_capital <= 0) AS average_loss,
    MAX(return_on_capital) AS best_trade,
    MIN(return_on_capital) AS worst_trade
FROM trades;
