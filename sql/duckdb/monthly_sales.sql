SELECT
    strftime(order_date, '%Y-%m') AS month,
    ROUND(
        SUM(
            quantity
            * CAST(unit_price AS DECIMAL(18, 6))
            * (1 - CAST(discount_pct AS DECIMAL(9, 6)))
        ),
        2
    ) AS total_revenue
FROM sales
GROUP BY month
ORDER BY month;
