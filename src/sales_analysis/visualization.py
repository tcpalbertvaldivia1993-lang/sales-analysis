"""Gráficos interactivos de ventas."""

import logging
from pathlib import Path

import pandas as pd
import plotly.express as px


def save_revenue_chart(monthly_sales: pd.DataFrame, output_path: Path) -> Path:
    """Guarda un gráfico HTML interactivo de ingresos mensuales."""
    if monthly_sales.empty:
        raise ValueError("No hay ventas mensuales para graficar.")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure = px.line(
        monthly_sales,
        x="month",
        y="total_revenue",
        markers=True,
        title="Ingresos netos por mes",
        labels={"month": "Mes", "total_revenue": "Ingresos"},
    )
    figure.update_layout(template="plotly_white", hovermode="x unified")
    figure.write_html(output, include_plotlyjs=True)
    logging.getLogger(__name__).info("Gráfico exportado: %s", output)
    return output
