from decimal import Decimal

import pandas as pd
import pytest

from src.sales_analysis.duckdb_analysis import analyze_sales
from src.sales_analysis.validation import SalesDataValidationError, validate_sales_data


@pytest.fixture
def valid_sales() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "order_id": "O-1", "order_date": "2025-01-10", "customer_id": "C-1",
                "customer_name": "Cliente de prueba", "region": "Sur", "product_id": "P-1",
                "product_name": "Café", "category": "Alimentos", "quantity": 2,
                "unit_price": 10.0, "discount_pct": 0.0,
            },
            {
                "order_id": "O-1", "order_date": "2025-01-10", "customer_id": "C-1",
                "customer_name": "Cliente de prueba", "region": "Sur", "product_id": "P-2",
                "product_name": "Té", "category": "Alimentos", "quantity": 1,
                "unit_price": 5.0, "discount_pct": 0.0,
            },
            {
                "order_id": "O-2", "order_date": "2025-02-03", "customer_id": "C-2",
                "customer_name": "Otro cliente", "region": "Norte", "product_id": "P-1",
                "product_name": "Café", "category": "Alimentos", "quantity": 3,
                "unit_price": 10.0, "discount_pct": 0.1,
            },
        ]
    )


def test_validation_parses_dates_and_quantity(valid_sales: pd.DataFrame) -> None:
    cleaned = validate_sales_data(valid_sales)
    assert pd.api.types.is_datetime64_any_dtype(cleaned["order_date"])
    assert cleaned["quantity"].dtype == "int64"


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("order_id", None, "nulos o vacíos"),
        ("order_date", "fecha-invalida", "fechas inválidas"),
        ("unit_price", "no-es-precio", "no numéricos"),
        ("unit_price", -2, "importe finito no negativo"),
    ],
)
def test_validation_rejects_invalid_values(
    valid_sales: pd.DataFrame, column: str, value: object, message: str
) -> None:
    invalid = valid_sales.copy()
    if column == "unit_price" and isinstance(value, str):
        invalid[column] = invalid[column].astype("object")
    invalid.loc[0, column] = value
    with pytest.raises(SalesDataValidationError, match=message):
        validate_sales_data(invalid)


def test_validation_rejects_missing_columns(valid_sales: pd.DataFrame) -> None:
    with pytest.raises(SalesDataValidationError, match="Faltan columnas"):
        validate_sales_data(valid_sales.drop(columns="region"))


def test_quantity_accepts_int64_max_before_conversion(valid_sales: pd.DataFrame) -> None:
    boundary = valid_sales.copy()
    boundary["quantity"] = boundary["quantity"].astype("object")
    boundary.loc[0, "quantity"] = str(2**63 - 1)

    cleaned = validate_sales_data(boundary)

    assert cleaned.loc[0, "quantity"] == 2**63 - 1
    assert cleaned["quantity"].dtype == "int64"


def test_validation_accepts_zero_with_extra_trailing_decimal_zeros(
    valid_sales: pd.DataFrame,
) -> None:
    zero_values = valid_sales.iloc[[0]].copy()
    zero_values["unit_price"] = zero_values["unit_price"].astype("object")
    zero_values["discount_pct"] = zero_values["discount_pct"].astype("object")
    zero_values.loc[0, "unit_price"] = "0.0000000"
    zero_values.loc[0, "discount_pct"] = "0.00000000"

    cleaned = validate_sales_data(zero_values)

    assert cleaned.loc[0, "unit_price"] == Decimal("0")
    assert cleaned.loc[0, "discount_pct"] == Decimal("0")


@pytest.mark.parametrize(
    ("quantity", "message"),
    [
        (str(2**63), "rango int64"),
        ("1.5", "entero positivo"),
        ("0", "entero positivo"),
        ("Infinity", "no finitos"),
        ("NaN", "no finitos"),
    ],
)
def test_validation_rejects_quantity_outside_safe_integer_domain(
    valid_sales: pd.DataFrame, quantity: str, message: str
) -> None:
    invalid = valid_sales.copy()
    invalid["quantity"] = invalid["quantity"].astype("object")
    invalid.loc[0, "quantity"] = quantity

    with pytest.raises(SalesDataValidationError, match=message):
        validate_sales_data(invalid)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("unit_price", "Infinity", "no finitos"),
        ("unit_price", "0.0000001", "DECIMAL\\(18, 6\\)"),
        ("discount_pct", "-Infinity", "no finitos"),
    ],
)
def test_validation_rejects_non_finite_or_unrepresentable_amounts(
    valid_sales: pd.DataFrame, column: str, value: str, message: str
) -> None:
    invalid = valid_sales.copy()
    invalid[column] = invalid[column].astype("object")
    invalid.loc[0, column] = value

    with pytest.raises(SalesDataValidationError, match=message):
        validate_sales_data(invalid)


def test_validation_rejects_line_revenue_beyond_decimal_range(
    valid_sales: pd.DataFrame,
) -> None:
    invalid = valid_sales.copy()
    invalid["quantity"] = invalid["quantity"].astype("object")
    invalid["unit_price"] = invalid["unit_price"].astype("object")
    invalid.loc[0, "quantity"] = str(2**63 - 1)
    invalid.loc[0, "unit_price"] = "999999999999.999999"

    with pytest.raises(SalesDataValidationError, match="rango monetario seguro"):
        validate_sales_data(invalid)


def test_duckdb_metrics_and_top_products(valid_sales: pd.DataFrame) -> None:
    result = analyze_sales(validate_sales_data(valid_sales))
    assert result.total_revenue == 52.0
    assert result.sale_count == 2
    assert result.average_ticket == 26.0
    assert result.top_products.iloc[0]["product_name"] == "Café"
    assert result.top_products.iloc[0]["units_sold"] == 5
    assert isinstance(result.top_products.iloc[0]["total_revenue"], Decimal)
    assert len(result.monthly_sales) == 2
    assert isinstance(result.monthly_sales.iloc[0]["total_revenue"], Decimal)


def test_product_name_variants_are_reported_without_splitting_product(
    valid_sales: pd.DataFrame,
) -> None:
    sales = valid_sales.iloc[:2].copy()
    sales.loc[1, "product_id"] = "P-1"
    sales.loc[1, "product_name"] = "Cafe molido"

    result = analyze_sales(validate_sales_data(sales))

    product = result.top_products.loc[result.top_products["product_id"] == "P-1"].iloc[0]
    assert product["units_sold"] == 3
    assert set(product["product_name"].split(" | ")) == {"Café", "Cafe molido"}
    assert product["has_name_conflict"]


def test_products_with_different_ids_remain_separate(
    valid_sales: pd.DataFrame,
) -> None:
    result = analyze_sales(validate_sales_data(valid_sales))

    products = result.top_products.set_index("product_id")
    assert set(products.index) == {"P-1", "P-2"}
    assert products.loc["P-1", "units_sold"] == 5
    assert products.loc["P-2", "units_sold"] == 1
    assert not products.loc["P-1", "has_name_conflict"]
    assert not products.loc["P-2", "has_name_conflict"]


def test_duckdb_uses_decimal_arithmetic_for_money(valid_sales: pd.DataFrame) -> None:
    exact_sales = valid_sales.iloc[[0]].copy()
    exact_sales["quantity"] = 3
    exact_sales["unit_price"] = exact_sales["unit_price"].astype("object")
    exact_sales["discount_pct"] = exact_sales["discount_pct"].astype("object")
    exact_sales["unit_price"] = "0.10"
    exact_sales["discount_pct"] = "0.100000"

    result = analyze_sales(validate_sales_data(exact_sales))

    assert result.total_revenue == Decimal("0.27")
    assert result.average_ticket == Decimal("0.27")
    assert isinstance(result.total_revenue, Decimal)
