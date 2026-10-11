PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sales (
    sale_line_id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL,
    order_date TEXT NOT NULL CHECK (date(order_date) IS NOT NULL),
    customer_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    region TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    discount_pct REAL NOT NULL DEFAULT 0 CHECK (discount_pct >= 0 AND discount_pct <= 1),
    loaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sales_order_date ON sales(order_date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_region ON sales(region);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
