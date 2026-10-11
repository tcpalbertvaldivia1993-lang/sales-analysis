SELECT
    region,
    COUNT(DISTINCT order_id) AS orders,
    SUM(quantity) AS units,
    ROUND(SUM(quantity * unit_price * (1 - discount_pct)), 2) AS net_revenue
FROM sales
GROUP BY region
ORDER BY net_revenue DESC;
