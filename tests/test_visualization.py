from decimal import Decimal
from pathlib import Path

import pandas as pd

from src.sales_analysis.exploratory import analyze_exploratory_sales
from src.sales_analysis.validation import validate_sales_data
from src.sales_analysis.visualization import save_sales_dashboard


def test_dashboard_is_self_contained_interactive_and_excludes_identifiers(
    tmp_path: Path,
) -> None:
    sales = pd.DataFrame([
        {
            "order_id": "ORDER-PRIVATE-1", "order_date": "2025-01-10",
            "customer_id": "CUSTOMER-PRIVATE-1", "customer_name": "Nombre privado único",
            "region": "Norte", "product_id": "P-1", "product_name": "Café",
            "category": "Alimentos", "quantity": 2, "unit_price": "10.00",
            "discount_pct": "0.100000",
        },
        {
            "order_id": "ORDER-PRIVATE-1", "order_date": "2025-01-10",
            "customer_id": "CUSTOMER-PRIVATE-1", "customer_name": "Nombre privado único",
            "region": "Norte", "product_id": "P-2", "product_name": "Té",
            "category": "Alimentos", "quantity": 1, "unit_price": "5.00",
            "discount_pct": "0.200000",
        },
        {
            "order_id": "ORDER-PRIVATE-2", "order_date": "2025-02-01",
            "customer_id": "CUSTOMER-PRIVATE-2", "customer_name": "Otro nombre privado",
            "region": "Sur", "product_id": "P-2", "product_name": "Té",
            "category": "Alimentos", "quantity": 3, "unit_price": "0.50",
            "discount_pct": "0.200000",
        },
    ])
    analysis = analyze_exploratory_sales(validate_sales_data(sales))
    output_path = tmp_path / "nested" / "dashboard.html"

    assert save_sales_dashboard(analysis, output_path) == output_path

    html = output_path.read_text(encoding="utf-8")
    assert "plotly.js" in html.lower()
    assert 'id="region-filter"' in html
    assert 'id="product-filter"' in html
    assert 'id="kpi-revenue"' in html
    assert 'id="kpi-orders"' in html
    assert 'id="kpi-ticket"' in html
    assert 'id="kpi-units"' in html
    assert "Plotly.restyle" in html
    assert "Ingresos netos por mes" in html
    assert r"Comparaci\u00f3n de ingresos netos por regi\u00f3n" in html
    assert r"Comparaci\u00f3n de ingresos netos por producto" in html

    for private_value in (
        "ORDER-PRIVATE-1",
        "CUSTOMER-PRIVATE-1",
        "Nombre privado único",
        "Otro nombre privado",
        "customer_id",
        "customer_name",
        "order_id",
    ):
        assert private_value not in html


def test_dashboard_filter_with_no_matching_rows_has_zero_metrics_and_empty_state(
    tmp_path: Path,
) -> None:
    sales = pd.DataFrame([
        {
            "order_id": "O-NORTE", "order_date": "2025-01-10",
            "customer_id": "C-1", "customer_name": "Cliente uno", "region": "Norte",
            "product_id": "P-1", "product_name": "Café", "category": "Alimentos",
            "quantity": 1, "unit_price": "10.00", "discount_pct": "0",
        },
        {
            "order_id": "O-SUR", "order_date": "2025-02-10",
            "customer_id": "C-2", "customer_name": "Cliente dos", "region": "Sur",
            "product_id": "P-2", "product_name": "Té", "category": "Alimentos",
            "quantity": 2, "unit_price": "5.00", "discount_pct": "0.100000",
        },
    ])
    analysis = analyze_exploratory_sales(validate_sales_data(sales))
    metrics = {
        (row["region_filter"], row["product_filter"]): row
        for row in analysis.dashboard_filter_metrics
    }

    assert ("Norte", "P-2") not in metrics
    assert metrics[(None, None)]["total_revenue"] == Decimal("19.00")
    output_path = tmp_path / "dashboard.html"
    save_sales_dashboard(analysis, output_path)
    html = output_path.read_text(encoding="utf-8")

    assert "No hay ventas para la combinación de filtros seleccionada." in html
    assert 'emptyState.hidden = hasResults' in html
    assert 'hasResults ? summary.sale_count : 0' in html
