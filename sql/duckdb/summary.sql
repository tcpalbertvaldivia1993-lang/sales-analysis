SELECT
    SUM(
        quantity
        * CAST(unit_price AS DECIMAL(18, 6))
        * (1 - CAST(discount_pct AS DECIMAL(9, 6)))
    ) AS net_revenue_unrounded,
    COUNT(DISTINCT order_id) AS sale_count
FROM sales;
