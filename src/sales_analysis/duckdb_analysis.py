"""Métricas y consultas analíticas SQL ejecutadas con DuckDB."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path

import duckdb
import pandas as pd

SQL_DIR = Path(__file__).resolve().parents[2] / "sql" / "duckdb"


@dataclass(frozen=True)
class SalesAnalysis:
    """Resultados tabulares y métricas agregadas del análisis."""

    total_revenue: Decimal
    sale_count: int
    average_ticket: Decimal
    top_products: pd.DataFrame
    monthly_sales: pd.DataFrame


def _run_query(connection: duckdb.DuckDBPyConnection, filename: str) -> pd.DataFrame:
    query = (SQL_DIR / filename).read_text(encoding="utf-8")
    cursor = connection.execute(query)
    columns = [column[0] for column in cursor.description]
    return pd.DataFrame.from_records(cursor.fetchall(), columns=columns)


def _run_summary(connection: duckdb.DuckDBPyConnection) -> tuple[Decimal, int, Decimal]:
    query = (SQL_DIR / "summary.sql").read_text(encoding="utf-8")
    net_revenue, sale_count = connection.execute(query).fetchone()
    sale_count = int(sale_count)
    cents = Decimal("0.01")
    with localcontext() as context:
        context.prec = 50
        total_revenue = net_revenue.quantize(cents, rounding=ROUND_HALF_UP)
        average_ticket = (net_revenue / sale_count).quantize(cents, rounding=ROUND_HALF_UP)
    return total_revenue, sale_count, average_ticket


def analyze_sales(sales: pd.DataFrame) -> SalesAnalysis:
    """Calcula ingresos, pedidos, ticket medio, ranking y ventas mensuales."""
    if sales.empty:
        raise ValueError("No hay datos para analizar.")

    with duckdb.connect(database=":memory:") as connection:
        connection.register("sales_input", sales)
        connection.execute("CREATE TABLE sales AS SELECT * FROM sales_input")
        total_revenue, sale_count, average_ticket = _run_summary(connection)
        top_products = _run_query(connection, "top_products.sql")
        monthly_sales = _run_query(connection, "monthly_sales.sql")

    return SalesAnalysis(
        total_revenue=total_revenue,
        sale_count=sale_count,
        average_ticket=average_ticket,
        top_products=top_products,
        monthly_sales=monthly_sales,
    )
