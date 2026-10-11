"""Dashboard interactivo y autocontenido de ventas."""

import json
import logging
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from .exploratory import ExploratoryAnalysis


def _round_money(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _totals_by(cube: pd.DataFrame, column: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in cube.itertuples(index=False):
        key = str(getattr(row, column))
        totals[key] = totals.get(key, Decimal(0)) + row.total_revenue
    return totals


def _initial_figure(cube: pd.DataFrame) -> go.Figure:
    monthly = _totals_by(cube, "month")
    regions = _totals_by(cube, "region")
    products = _totals_by(cube, "product_id")
    product_labels = {
        str(row.product_id): f"{row.product_id} — {row.product_name}"
        for row in cube.drop_duplicates("product_id").itertuples(index=False)
    }

    figure = make_subplots(
        rows=3,
        cols=1,
        vertical_spacing=0.13,
        subplot_titles=(
            "Ingresos netos por mes",
            "Comparación de ingresos netos por región",
            "Comparación de ingresos netos por producto",
        ),
    )
    figure.add_trace(
        go.Scatter(
            x=sorted(monthly),
            y=[float(_round_money(monthly[month])) for month in sorted(monthly)],
            mode="lines+markers",
            name="Ingresos netos",
            hovertemplate="%{x}<br>Ingresos netos: %{y:,.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    region_items = sorted(regions.items(), key=lambda item: (-item[1], item[0]))
    figure.add_trace(
        go.Bar(
            x=[float(_round_money(value)) for _, value in region_items],
            y=[region for region, _ in region_items],
            orientation="h",
            name="Ingresos por región",
            hovertemplate="%{y}<br>Ingresos netos: %{x:,.2f}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    product_items = sorted(products.items(), key=lambda item: (-item[1], item[0]))
    figure.add_trace(
        go.Bar(
            x=[float(_round_money(value)) for _, value in product_items],
            y=[product_labels[product_id] for product_id, _ in product_items],
            orientation="h",
            name="Ingresos por producto",
            hovertemplate="%{y}<br>Ingresos netos: %{x:,.2f}<extra></extra>",
        ),
        row=3,
        col=1,
    )

    figure.update_layout(
        template="plotly_white",
        height=1050,
        showlegend=False,
        margin={"l": 35, "r": 30, "t": 70, "b": 35},
        hovermode="closest",
        bargap=0.3,
    )
    figure.update_xaxes(title_text="Mes", row=1, col=1)
    figure.update_yaxes(title_text="Ingresos netos", tickformat=",.2f", row=1, col=1)
    figure.update_xaxes(title_text="Ingresos netos", tickformat=",.2f", row=2, col=1)
    figure.update_xaxes(title_text="Ingresos netos", tickformat=",.2f", row=3, col=1)
    figure.update_yaxes(autorange="reversed", row=2, col=1)
    figure.update_yaxes(autorange="reversed", row=3, col=1)
    return figure


def _dashboard_payload(analysis: ExploratoryAnalysis) -> dict[str, object]:
    cube = [
        {
            "month": str(row.month),
            "region": str(row.region),
            "product_id": str(row.product_id),
            "units_sold": int(row.units_sold),
            "total_revenue": format(row.total_revenue, "f"),
        }
        for row in analysis.dashboard_cube.itertuples(index=False)
    ]
    products = [
        {
            "product_id": str(row.product_id),
            "product_name": str(row.product_name),
            "has_name_conflict": bool(row.has_name_conflict),
        }
        for row in analysis.sales_by_product.itertuples(index=False)
    ]
    metrics = [
        {
            "region_filter": row["region_filter"],
            "product_filter": row["product_filter"],
            "total_revenue": format(row["total_revenue"], "f"),
            "sale_count": int(row["sale_count"]),
            "average_ticket": (
                format(row["average_ticket"], "f")
                if row["average_ticket"] is not None
                else None
            ),
            "units_sold": int(row["units_sold"]),
        }
        for row in analysis.dashboard_filter_metrics
    ]
    return {
        "cube": cube,
        "products": products,
        "regions": sorted({row["region"] for row in cube}),
        "filter_metrics": metrics,
    }


def _json_for_html(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return serialized.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")


def _dashboard_html(figure: go.Figure, payload: dict[str, object]) -> str:
    payload_json = _json_for_html(payload)
    chart_html = pio.to_html(
        figure,
        full_html=False,
        include_plotlyjs=True,
        config={"responsive": True, "displaylogo": False},
        div_id="sales-dashboard-chart",
    )

    template = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard de análisis de ventas</title>
  <style>
    :root { color-scheme: light; font-family: Inter, Segoe UI, Arial, sans-serif; color: #172033; background: #f3f6fb; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #f3f6fb; }
    main { width: min(1440px, calc(100% - 40px)); margin: 0 auto; padding: 34px 0 48px; }
    header { padding: 30px 34px; color: #fff; border-radius: 18px; background: linear-gradient(120deg, #14213d, #244a73); box-shadow: 0 14px 34px #14213d20; }
    .eyebrow { margin: 0 0 8px; color: #a9c8e8; font-size: 12px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
    h1 { margin: 0; font-size: clamp(25px, 4vw, 38px); }
    .subtitle { margin: 10px 0 0; color: #d4e1ee; }
    .filters { display: flex; flex-wrap: wrap; gap: 16px; margin: 24px 0 18px; padding: 18px 20px; border: 1px solid #e1e7f0; border-radius: 14px; background: #fff; }
    .filter { display: grid; min-width: min(260px, 100%); gap: 7px; }
    label { color: #596579; font-size: 13px; font-weight: 650; }
    select { min-height: 42px; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 8px; color: #172033; background: #fff; font: inherit; }
    .kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 18px 0; }
    .kpi { min-height: 112px; padding: 19px 20px; border: 1px solid #e1e7f0; border-radius: 14px; background: #fff; box-shadow: 0 4px 14px #14213d08; }
    .kpi-label { color: #647087; font-size: 13px; }
    .kpi-value { display: block; margin-top: 12px; color: #14213d; font-size: clamp(21px, 3vw, 30px); font-weight: 750; font-variant-numeric: tabular-nums; }
    .chart-card { overflow: hidden; padding: 12px; border: 1px solid #e1e7f0; border-radius: 14px; background: #fff; }
    #empty-state { margin: 0 0 12px; padding: 12px 16px; border-radius: 8px; color: #805b16; background: #fff7df; }
    #empty-state[hidden] { display: none; }
    footer { margin-top: 14px; color: #647087; font-size: 12px; }
    @media (max-width: 800px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } main { width: min(100% - 24px, 1440px); padding-top: 16px; } header { padding: 24px; } }
    @media (max-width: 460px) { .kpis { grid-template-columns: 1fr 1fr; gap: 8px; } .kpi { padding: 14px; } .kpi-label { font-size: 11px; } }
  </style>
</head>
<body>
<main>
  <header>
    <p class="eyebrow">Sales analysis · Python + DuckDB</p>
    <h1>Dashboard de análisis de ventas</h1>
    <p class="subtitle">Explora ingresos netos, pedidos, ticket promedio y unidades vendidas.</p>
  </header>
  <section class="filters" aria-label="Filtros del dashboard">
    <div class="filter">
      <label for="region-filter">Región</label>
      <select id="region-filter"><option value="">Todas las regiones</option></select>
    </div>
    <div class="filter">
      <label for="product-filter">Producto</label>
      <select id="product-filter"><option value="">Todos los productos</option></select>
    </div>
  </section>
  <section class="kpis" aria-label="Indicadores principales">
    <article class="kpi"><span class="kpi-label">Ingresos netos</span><strong class="kpi-value" id="kpi-revenue">—</strong></article>
    <article class="kpi"><span class="kpi-label">Pedidos distintos</span><strong class="kpi-value" id="kpi-orders">—</strong></article>
    <article class="kpi"><span class="kpi-label">Ticket promedio</span><strong class="kpi-value" id="kpi-ticket">—</strong></article>
    <article class="kpi"><span class="kpi-label">Unidades vendidas</span><strong class="kpi-value" id="kpi-units">—</strong></article>
  </section>
  <section class="chart-card" aria-label="Gráficos comparativos de ventas">
    <p id="empty-state" role="status" hidden>No hay ventas para la combinación de filtros seleccionada.</p>
    __CHART__
  </section>
  <footer>Los importes muestran ingresos netos sin símbolo monetario; el archivo es local y funciona sin conexión.</footer>
</main>
<script type="application/json" id="dashboard-data">__PAYLOAD__</script>
<script>
(() => {
  const payload = JSON.parse(document.getElementById("dashboard-data").textContent);
  const regionSelect = document.getElementById("region-filter");
  const productSelect = document.getElementById("product-filter");
  const emptyState = document.getElementById("empty-state");
  const numberFormat = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 0 });
  const amountFormat = new Intl.NumberFormat("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const metrics = new Map(payload.filter_metrics.map((row) => [
    JSON.stringify([row.region_filter, row.product_filter]), row
  ]));
  const productLabels = new Map(payload.products.map((row) => [
    row.product_id,
    row.has_name_conflict
      ? `${row.product_id} — ${row.product_name} (nombres distintos)`
      : `${row.product_id} — ${row.product_name}`
  ]));

  for (const region of payload.regions) {
    const option = document.createElement("option");
    option.value = region;
    option.textContent = region;
    regionSelect.appendChild(option);
  }
  for (const product of payload.products) {
    const option = document.createElement("option");
    option.value = product.product_id;
    option.textContent = productLabels.get(product.product_id);
    productSelect.appendChild(option);
  }

  const chart = document.getElementById("sales-dashboard-chart");
  const roundForChart = (value) => Math.round((value + Number.EPSILON) * 100) / 100;
  const render = () => {
    const region = regionSelect.value || null;
    const product = productSelect.value || null;
    const filtered = payload.cube.filter((row) =>
      (region === null || row.region === region) &&
      (product === null || row.product_id === product)
    );
    const summary = metrics.get(JSON.stringify([region, product]));
    const hasResults = filtered.length > 0 && summary && summary.sale_count > 0;

    document.getElementById("kpi-revenue").textContent = amountFormat.format(
      Number(hasResults ? summary.total_revenue : "0")
    );
    document.getElementById("kpi-orders").textContent = numberFormat.format(
      hasResults ? summary.sale_count : 0
    );
    document.getElementById("kpi-ticket").textContent = hasResults && summary.average_ticket !== null
      ? amountFormat.format(Number(summary.average_ticket))
      : "—";
    document.getElementById("kpi-units").textContent = numberFormat.format(
      hasResults ? summary.units_sold : 0
    );
    emptyState.hidden = hasResults;

    const totals = (key) => {
      const grouped = new Map();
      for (const row of filtered) {
        const groupKey = key(row);
        const current = grouped.get(groupKey) || 0;
        grouped.set(groupKey, current + Number(row.total_revenue));
      }
      return grouped;
    };
    const monthly = totals((row) => row.month);
    const byRegion = totals((row) => row.region);
    const byProduct = totals((row) => row.product_id);
    const months = [...monthly.keys()].sort();
    const regions = [...byRegion.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    const products = [...byProduct.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));

    Plotly.restyle(chart, {
      x: [months],
      y: [months.map((month) => roundForChart(monthly.get(month)))],
    }, [0]);
    Plotly.restyle(chart, {
      x: [regions.map(([, value]) => roundForChart(value))],
      y: [regions.map(([name]) => name)],
    }, [1]);
    Plotly.restyle(chart, {
      x: [products.map(([, value]) => roundForChart(value))],
      y: [products.map(([productId]) => productLabels.get(productId) || productId)],
    }, [2]);
  };

  regionSelect.addEventListener("change", render);
  productSelect.addEventListener("change", render);
  window.addEventListener("load", render, { once: true });
})();
</script>
</body>
</html>
"""
    return template.replace("__CHART__", chart_html).replace("__PAYLOAD__", payload_json)


def save_sales_dashboard(analysis: ExploratoryAnalysis, output_path: Path) -> Path:
    """Guarda un dashboard interactivo autocontenido usando solo datos agregados."""
    if analysis.dashboard_cube.empty:
        raise ValueError("No hay ventas agregadas para generar el dashboard.")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure = _initial_figure(analysis.dashboard_cube)
    page = _dashboard_html(figure, _dashboard_payload(analysis))
    output.write_text(page, encoding="utf-8")
    logging.getLogger(__name__).info("Dashboard exportado: %s", output)
    return output
