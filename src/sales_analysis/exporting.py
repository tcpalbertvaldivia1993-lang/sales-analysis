"""Exportación de tablas del análisis exploratorio a CSV."""

from pathlib import Path

from .exploratory import ExploratoryAnalysis

CSV_OUTPUT_FILENAMES = {
    "revenue_by_region": "ventas_por_region.csv",
    "sales_by_product": "metricas_por_producto.csv",
    "top_customers": "top_5_clientes.csv",
}


def exploratory_csv_paths(output_dir: Path) -> dict[str, Path]:
    """Devuelve las rutas de los tres CSV del análisis exploratorio."""
    directory = Path(output_dir)
    return {
        name: directory / filename
        for name, filename in CSV_OUTPUT_FILENAMES.items()
    }


def save_exploratory_csvs(analysis: ExploratoryAnalysis, output_dir: Path) -> dict[str, Path]:
    """Guarda las tablas exploratorias sin incluir índices de pandas."""
    paths = exploratory_csv_paths(output_dir)
    paths["revenue_by_region"].parent.mkdir(parents=True, exist_ok=True)

    analysis.revenue_by_region.to_csv(paths["revenue_by_region"], index=False)
    analysis.sales_by_product.to_csv(paths["sales_by_product"], index=False)
    analysis.top_customers.to_csv(paths["top_customers"], index=False)
    return paths
