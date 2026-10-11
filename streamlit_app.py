"""Aplicación web para cargar ventas y explorar resultados sin guardar archivos."""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
import pandas as pd

from src.sales_analysis.duckdb_analysis import analyze_sales
from src.sales_analysis.exploratory import analyze_exploratory_sales
from src.sales_analysis.validation import SalesDataValidationError, validate_sales_data
from src.sales_analysis.visualization import save_sales_dashboard


@dataclass(frozen=True)
class WebResults:
    """Artefactos presentables y descargables sin datos identificativos de clientes."""

    dashboard_html: bytes
    revenue_by_region_csv: bytes
    sales_by_product_csv: bytes
    total_revenue: str
    order_count: int
    average_ticket: str


def _read_uploaded_csv(content: bytes) -> pd.DataFrame:
    """Lee una carga web y aplica el mismo validador que el flujo local."""
    try:
        data = pd.read_csv(
            BytesIO(content),
            encoding="utf-8-sig",
            dtype={"quantity": "string", "unit_price": "string", "discount_pct": "string"},
        )
    except pd.errors.EmptyDataError as exc:
        raise SalesDataValidationError("El archivo CSV está vacío.") from exc
    return validate_sales_data(data)


def _csv_bytes(frame: pd.DataFrame) -> bytes:
    """Serializa una tabla sin índice para ofrecerla como descarga web."""
    return frame.to_csv(index=False).encode("utf-8-sig")


def build_web_results(content: bytes) -> WebResults:
    """Valida y analiza un CSV, devolviendo únicamente resultados agregados."""
    sales = _read_uploaded_csv(content)
    exploratory = analyze_exploratory_sales(sales)
    duckdb_results = analyze_sales(sales)

    with TemporaryDirectory(prefix="sales-analysis-") as temporary_directory:
        dashboard_path = Path(temporary_directory) / "dashboard.html"
        save_sales_dashboard(exploratory, dashboard_path)
        dashboard_html = dashboard_path.read_bytes()

    # El informe de clientes contiene datos personales y se conserva solo en el
    # flujo local existente; la aplicación web ofrece únicamente tablas agregadas.
    return WebResults(
        dashboard_html=dashboard_html,
        revenue_by_region_csv=_csv_bytes(exploratory.revenue_by_region),
        sales_by_product_csv=_csv_bytes(exploratory.sales_by_product),
        total_revenue=f"{duckdb_results.total_revenue:.2f}",
        order_count=duckdb_results.sale_count,
        average_ticket=f"{duckdb_results.average_ticket:.2f}",
    )


def main() -> None:
    """Renderiza la app Streamlit; la importación se difiere para facilitar pruebas."""
    import streamlit as st

    st.set_page_config(page_title="Análisis de ventas", page_icon="📊", layout="wide")
    st.title("Dashboard de análisis de ventas")
    st.write(
        "Carga un CSV para validar y explorar sus ventas. El dashboard muestra "
        "resultados agregados y no presenta datos personales de clientes."
    )

    with st.form("sales-upload-form"):
        uploaded_file = st.file_uploader("Archivo CSV de ventas", type=["csv"])
        submitted = st.form_submit_button("Analizar ventas")

    if submitted:
        if uploaded_file is None:
            st.session_state.pop("sales_results", None)
            st.error("Selecciona un archivo CSV para iniciar el análisis.")
        else:
            try:
                st.session_state["sales_results"] = build_web_results(uploaded_file.getvalue())
            except (
                OSError,
                ValueError,
                duckdb.Error,
                pd.errors.ParserError,
            ) as exc:
                st.session_state.pop("sales_results", None)
                st.error(f"No se pudo completar el análisis: {exc}")

    results = st.session_state.get("sales_results")
    if results is None:
        st.info("Carga un CSV válido para ver el dashboard y descargar sus resultados.")
        return

    dashboard_tab, results_tab = st.tabs(["Dashboard interactivo", "Resumen y descargas"])
    with dashboard_tab:
        st.iframe(
            results.dashboard_html.decode("utf-8"),
            height=1550,
            alt="Dashboard interactivo de ventas con filtros y gráficos",
        )

    with results_tab:
        revenue_column, orders_column, ticket_column = st.columns(3)
        revenue_column.metric("Ingresos netos", results.total_revenue)
        orders_column.metric("Pedidos distintos", results.order_count)
        ticket_column.metric("Ticket promedio", results.average_ticket)
        st.caption("Importes sin símbolo monetario: el archivo de entrada no especifica moneda.")

        st.download_button(
            "Descargar ventas por región",
            data=results.revenue_by_region_csv,
            file_name="ventas_por_region.csv",
            mime="text/csv",
        )
        st.download_button(
            "Descargar métricas por producto",
            data=results.sales_by_product_csv,
            file_name="metricas_por_producto.csv",
            mime="text/csv",
        )
        st.caption(
            "La descarga de top_5_clientes.csv no está disponible en esta app para "
            "evitar exponer nombres o identificadores de clientes. El flujo local "
            "de main.py conserva esa exportación."
        )


if __name__ == "__main__":
    main()
