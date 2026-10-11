from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from streamlit_app import build_web_results
from src.sales_analysis.validation import SalesDataValidationError


CSV_CONTENT = """order_id,order_date,customer_id,customer_name,region,product_id,product_name,category,quantity,unit_price,discount_pct
PRIVATE-ORDER-1,2025-01-10,PRIVATE-CUSTOMER-1,Nombre cliente secreto,Norte,P-1,Café,Alimentos,2,10.00,0.100000
PRIVATE-ORDER-1,2025-01-10,PRIVATE-CUSTOMER-1,Nombre cliente secreto,Norte,P-2,Té,Alimentos,1,5.00,0.200000
PRIVATE-ORDER-2,2025-02-01,PRIVATE-CUSTOMER-2,Otro cliente secreto,Sur,P-2,Té,Alimentos,3,0.50,0.200000
"""


def test_web_results_reuse_analysis_and_exclude_customer_data() -> None:
    result = build_web_results(CSV_CONTENT.encode("utf-8"))

    assert result.total_revenue == "23.20"
    assert result.order_count == 2
    assert result.average_ticket == "11.60"
    html = result.dashboard_html.decode("utf-8")
    exports = (
        result.revenue_by_region_csv.decode("utf-8-sig")
        + result.sales_by_product_csv.decode("utf-8-sig")
    )
    for private_value in (
        "PRIVATE-ORDER-1",
        "PRIVATE-CUSTOMER-1",
        "Nombre cliente secreto",
        "Otro cliente secreto",
        "customer_id",
        "customer_name",
        "order_id",
    ):
        assert private_value not in html
        assert private_value not in exports

    assert "Ingresos netos por mes" in html
    assert "Comparación de ingresos netos" in html or r"Comparaci\u00f3n de ingresos netos" in html
    assert result.revenue_by_region_csv.startswith(b"\xef\xbb\xbfregion,")
    assert result.sales_by_product_csv.startswith(b"\xef\xbb\xbfproduct_id,")


def test_web_results_reuse_existing_csv_validation() -> None:
    with pytest.raises(SalesDataValidationError, match="Faltan columnas obligatorias"):
        build_web_results(b"foo,bar\n1,2\n")


def test_web_results_accepts_csv_with_utf8_bom() -> None:
    result = build_web_results(("\ufeff" + CSV_CONTENT).encode("utf-8"))

    assert result.order_count == 2
    assert b"Norte" in result.revenue_by_region_csv


def test_streamlit_app_renders_dashboard_and_safe_downloads() -> None:
    app_path = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    app = AppTest.from_file(str(app_path)).run()
    app.file_uploader[0].upload("ventas.csv", CSV_CONTENT.encode("utf-8"), "text/csv")
    app.button[0].click().run()

    assert not app.exception
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Ingresos netos", "23.20"),
        ("Pedidos distintos", "2"),
        ("Ticket promedio", "11.60"),
    ]
    assert [button.label for button in app.get("download_button")] == [
        "Descargar ventas por región",
        "Descargar métricas por producto",
    ]
    assert len(app.get("iframe")) == 1
