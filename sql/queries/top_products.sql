SELECT
    product_id,
    product_name,
    category,
    SUM(quantity) AS units,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(quantity * unit_price * (1 - discount_pct)), 2) AS net_revenue
FROM sales
GROUP BY product_id, product_name, category
ORDER BY net_revenue DESC, units DESC;
