from decimal import Decimal

import pandas as pd

from src.sales_analysis.exploratory import analyze_exploratory_sales
from src.sales_analysis.validation import validate_sales_data


def test_exploratory_metrics_use_net_revenue_and_groupings() -> None:
    sales = pd.DataFrame([
        {
            "order_id": "O-1", "order_date": "2025-01-10", "customer_id": "C-1",
            "customer_name": "Cliente 001", "region": "Sur", "product_id": "P-1",
            "product_name": "Café", "category": "Alimentos", "quantity": 2,
            "unit_price": "0.10", "discount_pct": "0.100000",
        },
        {
            "order_id": "O-2", "order_date": "2025-01-11", "customer_id": "C-1",
            "customer_name": "Cliente 001", "region": "Norte", "product_id": "P-1",
            "product_name": "Café molido", "category": "Alimentos", "quantity": 1,
            "unit_price": "1.00", "discount_pct": "0",
        },
        {
            "order_id": "O-3", "order_date": "2025-01-12", "customer_id": "C-2",
            "customer_name": "Cliente 002", "region": "Sur", "product_id": "P-2",
            "product_name": "Té", "category": "Alimentos", "quantity": 3,
            "unit_price": "0.50", "discount_pct": "0.200000",
        },
    ])

    result = analyze_exploratory_sales(validate_sales_data(sales))

    assert result.total_revenue == Decimal("2.38")
    regional = result.revenue_by_region.set_index("region")["total_revenue"]
    assert regional.to_dict() == {"Norte": Decimal("1.00"), "Sur": Decimal("1.38")}

    products = result.sales_by_product.set_index("product_id")
    assert products.loc["P-1", "units_sold"] == 3
    assert products.loc["P-1", "total_revenue"] == Decimal("1.18")
    assert products.loc["P-1", "product_name"] == "Café | Café molido"
    assert products.loc["P-1", "has_name_conflict"]
    assert products.loc["P-2", "units_sold"] == 3
    assert products.loc["P-2", "total_revenue"] == Decimal("1.20")
    assert not products.loc["P-2", "has_name_conflict"]

    top = result.top_customers
    assert len(top) == 2
    assert top.iloc[0]["customer_id"] == "C-2"
    assert top.iloc[0]["total_revenue"] == Decimal("1.20")
    assert top.iloc[1]["customer_id"] == "C-1"
    assert top.iloc[1]["total_revenue"] == Decimal("1.18")


def test_top_customers_returns_at_most_five() -> None:
    rows = []
    for index in range(6):
        rows.append({
            "order_id": f"O-{index}", "order_date": "2025-01-10",
            "customer_id": f"C-{index}", "customer_name": f"Cliente {index:03}",
            "region": "Sur", "product_id": "P-1", "product_name": "Café",
            "category": "Alimentos", "quantity": index + 1,
            "unit_price": "1.00", "discount_pct": "0",
        })

    result = analyze_exploratory_sales(validate_sales_data(pd.DataFrame(rows)))

    assert len(result.top_customers) == 5
    assert result.top_customers.iloc[0]["customer_id"] == "C-5"
