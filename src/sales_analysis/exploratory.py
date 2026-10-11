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
    dashboard_cube: pd.DataFrame
    dashboard_filter_metrics: tuple[dict[str, object], ...]


def _net_revenue(quantity: int, unit_price: Decimal, discount_pct: Decimal) -> Decimal:
    """Aplica la fórmula neta usada por las consultas SQL del proyecto."""
    return Decimal(int(quantity)) * unit_price * (Decimal(1) - discount_pct)


def _names_and_conflict(names: pd.Series) -> tuple[str, bool]:
    unique_names = sorted(set(names.astype(str)))
    return " | ".join(unique_names), len(unique_names) > 1


def _dashboard_cube(frame: pd.DataFrame, sales_by_product: pd.DataFrame) -> pd.DataFrame:
    """Agrega ventas por mes, región y producto sin conservar identificadores de pedido."""
    product_names = sales_by_product.set_index("product_id")["product_name"].to_dict()
    named_frame = frame.assign(month=frame["order_date"].dt.strftime("%Y-%m"))
    rows = []
    for (month, region, product_id), group in named_frame.groupby(
        ["month", "region", "product_id"], sort=True
    ):
        rows.append({
            "month": str(month),
            "region": str(region),
            "product_id": str(product_id),
            "product_name": str(product_names[product_id]),
            "units_sold": int(group["quantity"].sum()),
            "total_revenue": sum(group["net_revenue"], Decimal(0)),
        })
    return pd.DataFrame(
        rows,
        columns=[
            "month", "region", "product_id", "product_name", "units_sold", "total_revenue",
        ],
    )


def _dashboard_filter_metrics(frame: pd.DataFrame) -> tuple[dict[str, object], ...]:
    """Calcula indicadores exactos para filtros globales, individuales y combinados."""
    rows: list[dict[str, object]] = []

    def append_metrics(
        group: pd.DataFrame, region_filter: str | None, product_filter: str | None
    ) -> None:
        revenue = sum(group["net_revenue"], Decimal(0))
        sale_count = int(group["order_id"].nunique())
        average_ticket = (
            (revenue / sale_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if sale_count
            else None
        )
        rows.append({
            "region_filter": region_filter,
            "product_filter": product_filter,
            "total_revenue": revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "sale_count": sale_count,
            "average_ticket": average_ticket,
            "units_sold": int(group["quantity"].sum()),
        })

    append_metrics(frame, None, None)
    for region, group in frame.groupby("region", sort=True):
        append_metrics(group, str(region), None)
    for product_id, group in frame.groupby("product_id", sort=True):
        append_metrics(group, None, str(product_id))
    for (region, product_id), group in frame.groupby(
        ["region", "product_id"], sort=True
    ):
        append_metrics(group, str(region), str(product_id))
    return tuple(rows)


def analyze_exploratory_sales(sales: pd.DataFrame) -> ExploratoryAnalysis:
    """Calcula ingresos, agrupaciones regionales y de producto, y top clientes.

    ``sales`` debe ser un DataFrame validado por ``validate_sales_data`` para
    asegurar que cantidades e importes tengan tipos y rangos válidos.
    """
    if sales.empty:
        raise ValueError("No hay datos para analizar.")

    required = {
        "order_id", "order_date", "customer_id", "customer_name", "region",
        "product_id", "product_name", "quantity", "unit_price", "discount_pct",
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
        dashboard_cube = _dashboard_cube(frame, sales_by_product)
        dashboard_filter_metrics = _dashboard_filter_metrics(frame)

    return ExploratoryAnalysis(
        total_revenue=total_revenue,
        revenue_by_region=revenue_by_region,
        sales_by_product=sales_by_product,
        top_customers=top_customers,
        dashboard_cube=dashboard_cube,
        dashboard_filter_metrics=dashboard_filter_metrics,
    )
