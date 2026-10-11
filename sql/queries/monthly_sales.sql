SELECT
    substr(order_date, 1, 7) AS month,
    COUNT(DISTINCT order_id) AS orders,
    SUM(quantity) AS units,
    ROUND(SUM(quantity * unit_price), 2) AS gross_revenue,
    ROUND(SUM(quantity * unit_price * discount_pct), 2) AS discount_amount,
    ROUND(SUM(quantity * unit_price * (1 - discount_pct)), 2) AS net_revenue
FROM sales
GROUP BY month
ORDER BY month;
