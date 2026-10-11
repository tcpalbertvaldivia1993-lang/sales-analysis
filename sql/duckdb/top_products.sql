SELECT
    product_id,
    STRING_AGG(DISTINCT product_name, ' | ' ORDER BY product_name) AS product_name,
    COUNT(DISTINCT product_name) > 1 AS has_name_conflict,
    SUM(quantity)::BIGINT AS units_sold,
    ROUND(
        SUM(
            quantity
            * CAST(unit_price AS DECIMAL(18, 6))
            * (1 - CAST(discount_pct AS DECIMAL(9, 6)))
        ),
        2
    ) AS total_revenue
FROM sales
GROUP BY product_id
ORDER BY units_sold DESC, total_revenue DESC, product_name
LIMIT 10;
