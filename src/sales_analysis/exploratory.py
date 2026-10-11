"""Análisis exploratorio de ventas con agregaciones de pandas."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext

import pandas as pd


@dataclass(frozen=True)
class ExploratoryAnalysis:
    """Resultados de ventas agrupados para el análisis exploratorio."""

    total_revenue: Decimal
    revenue_by_region: pd.DataFrame
    sales_by_product: pd.DataFrame
    top_customers: pd.DataFrame


def _net_revenue(quantity: int, unit_price: Decimal, discount_pct: Decimal) -> Decimal:
    """Aplica la fórmula neta usada por las consultas SQL del proyecto."""
    return Decimal(int(quantity)) * unit_price * (Decimal(1) - discount_pct)


def _names_and_conflict(names: pd.Series) -> tuple[str, bool]:
    unique_names = sorted(set(names.astype(str)))
    return " | ".join(unique_names), len(unique_names) > 1


def analyze_exploratory_sales(sales: pd.DataFrame) -> ExploratoryAnalysis:
    """Calcula ingresos, agrupaciones regionales y de producto, y top clientes.

    ``sales`` debe ser un DataFrame validado por ``validate_sales_data`` para
    asegurar que cantidades e importes tengan tipos y rangos válidos.
    """
    if sales.empty:
        raise ValueError("No hay datos para analizar.")

    required = {
        "customer_id", "customer_name", "region", "product_id", "product_name",
        "quantity", "unit_price", "discount_pct",
    }
    missing = sorted(required - set(sales.columns))
    if missing:
        raise ValueError("Faltan columnas para el análisis exploratorio: " + ", ".join(missing))

    with localcontext() as context:
        context.prec = 50
        frame = sales.copy()
        frame["net_revenue"] = [
            _net_revenue(quantity, price, discount)
            for quantity, price, discount in zip(
                frame["quantity"], frame["unit_price"], frame["discount_pct"]
            )
        ]
        total_revenue = sum(frame["net_revenue"], Decimal(0)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        revenue_by_region = (
            frame.groupby("region", as_index=False, sort=True)["net_revenue"]
            .sum()
            .rename(columns={"net_revenue": "total_revenue"})
        )
        revenue_by_region["total_revenue"] = revenue_by_region["total_revenue"].map(
            lambda amount: amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

        product_rows = []
        for product_id, group in frame.groupby("product_id", sort=True):
            names, conflict = _names_and_conflict(group["product_name"])
            product_rows.append({
                "product_id": product_id,
                "product_name": names,
                "has_name_conflict": conflict,
                "units_sold": int(group["quantity"].sum()),
                "total_revenue": sum(group["net_revenue"], Decimal(0)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
            })
        sales_by_product = pd.DataFrame(
            product_rows,
            columns=["product_id", "product_name", "has_name_conflict", "units_sold", "total_revenue"],
        ).sort_values(
            ["units_sold", "total_revenue", "product_name"],
            ascending=[False, False, True],
            ignore_index=True,
        )

        customer_rows = []
        for customer_id, group in frame.groupby("customer_id", sort=True):
            names, conflict = _names_and_conflict(group["customer_name"])
            customer_rows.append({
                "customer_id": customer_id,
                "customer_name": names,
                "has_name_conflict": conflict,
                "total_revenue": sum(group["net_revenue"], Decimal(0)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
            })
        top_customers = pd.DataFrame(customer_rows).sort_values(
            ["total_revenue", "customer_id"], ascending=[False, True], ignore_index=True
        ).head(5)

    return ExploratoryAnalysis(
        total_revenue=total_revenue,
        revenue_by_region=revenue_by_region,
        sales_by_product=sales_by_product,
        top_customers=top_customers,
    )
