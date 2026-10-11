"""Punto de entrada del sistema de análisis de ventas."""

import argparse
import logging
import os
from pathlib import Path

import duckdb
import pandas as pd

from src.sales_analysis.duckdb_analysis import analyze_sales
from src.sales_analysis.exporting import exploratory_csv_paths, save_exploratory_csvs
from src.sales_analysis.exploratory import analyze_exploratory_sales
from src.sales_analysis.validation import load_and_validate_csv
from src.sales_analysis.visualization import save_revenue_chart

ROOT = Path(__file__).resolve().parent


def validate_output_paths(csv_path: Path, output_path: Path) -> None:
    """Rechaza destinos inválidos o que puedan reemplazar el CSV de entrada."""
    resolved_csv = Path(csv_path).resolve()
    resolved_output = Path(output_path).resolve()

    if os.path.normcase(str(resolved_csv)) == os.path.normcase(str(resolved_output)):
        raise ValueError(
            "La ruta de salida coincide con el CSV de entrada; "
            "elige otro archivo para evitar sobrescribirlo."
        )
    if resolved_output.suffix.lower() != ".html":
        raise ValueError("El archivo de salida debe tener la extensión .html.")
    for csv_output in exploratory_csv_paths(resolved_output.parent).values():
        resolved_csv_output = Path(csv_output).resolve()
        if os.path.normcase(str(resolved_csv)) == os.path.normcase(str(resolved_csv_output)):
            raise ValueError(
                "Una ruta CSV de salida coincide con el CSV de entrada; "
                "elige otro archivo para evitar sobrescribirlo."
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Análisis de ventas con pandas, DuckDB y Plotly")
    parser.add_argument(
        "--csv", type=Path, default=ROOT / "data/raw/ventas_demo.csv",
        help="Ruta al CSV de ventas (por defecto: data/raw/ventas_demo.csv)",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "reports/analisis_ventas_dashboard.html",
        help="Ruta del gráfico HTML interactivo",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    try:
        validate_output_paths(args.csv, args.output)
        sales = load_and_validate_csv(args.csv)
        exploratory = analyze_exploratory_sales(sales)
        results = analyze_sales(sales)
        save_revenue_chart(results.monthly_sales, args.output)
        save_exploratory_csvs(exploratory, args.output.parent)
    except (OSError, ValueError, duckdb.Error, pd.errors.ParserError) as exc:
        logger.error("No se pudo completar el análisis: %s", exc)
        return 1

    print("\nResumen de ventas")
    print(f"Ingresos totales: {results.total_revenue:,.2f}")
    print(f"Número de ventas (pedidos): {results.sale_count}")
    print(f"Ticket promedio: {results.average_ticket:,.2f}")
    print(f"Ingresos netos (análisis pandas): {exploratory.total_revenue:,.2f}")
    print("\nIngresos netos por región:")
    print(exploratory.revenue_by_region.to_string(index=False))
    print("\nUnidades e ingresos netos por producto:")
    print(exploratory.sales_by_product.to_string(index=False))
    print("\nCinco clientes con mayor gasto neto:")
    print(exploratory.top_customers.to_string(index=False))
    print("\nProductos más vendidos (unidades):")
    print(results.top_products.to_string(index=False))
    logger.info("Gráfico interactivo guardado en %s", args.output)
    logger.info("Tablas CSV guardadas en %s", args.output.parent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
