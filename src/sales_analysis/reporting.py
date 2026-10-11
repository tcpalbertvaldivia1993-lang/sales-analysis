"""Consultas para el resumen ejecutivo."""

import csv
import sqlite3
from pathlib import Path


def summary(connection: sqlite3.Connection) -> dict[str, float | int | None]:
    row = connection.execute(
        """SELECT COUNT(DISTINCT order_id), COUNT(DISTINCT customer_id),
                  COALESCE(SUM(quantity), 0),
                  ROUND(COALESCE(SUM(quantity * unit_price * (1 - discount_pct)), 0), 2)
           FROM sales"""
    ).fetchone()
    orders, customers, units, revenue = row
    return {
        "orders": orders,
        "customers": customers,
        "units": units,
        "net_revenue": revenue,
        "average_order_value": round(revenue / orders, 2) if orders else None,
    }


def write_summary(connection: sqlite3.Connection, output_path: Path) -> dict[str, float | int | None]:
    metrics = summary(connection)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=metrics.keys())
        writer.writeheader()
        writer.writerow(metrics)
    return metrics
