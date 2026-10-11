import csv
from pathlib import Path

import pytest

from main import main


CSV_CONTENT = """order_id,order_date,customer_id,customer_name,region,product_id,product_name,category,quantity,unit_price,discount_pct
O-1,2025-01-10,C-1,Cliente de prueba,Sur,P-1,Café,Alimentos,2,10.00,0
"""


def test_main_rejects_output_that_resolves_to_input_csv(
    tmp_path: Path, monkeypatch, caplog
) -> None:
    csv_path = tmp_path / "ventas.csv"
    csv_path.write_text(CSV_CONTENT, encoding="utf-8")
    equivalent_path = tmp_path / "subdir" / ".." / "ventas.csv"
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "--csv", str(csv_path), "--output", str(equivalent_path)],
    )

    assert main() == 1
    assert "coincide con el CSV de entrada" in caplog.text
    assert csv_path.read_text(encoding="utf-8") == CSV_CONTENT


def test_main_rejects_output_without_html_extension(
    tmp_path: Path, monkeypatch, caplog
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--csv",
            str(tmp_path / "no-es-necesario.csv"),
            "--output",
            str(tmp_path / "grafico.png"),
        ],
    )

    assert main() == 1
    assert "debe tener la extensión .html" in caplog.text


@pytest.mark.parametrize(
    "filename",
    [
        "ventas_por_region.csv",
        "metricas_por_producto.csv",
        "top_5_clientes.csv",
    ],
)
def test_main_rejects_csv_output_that_resolves_to_input(
    tmp_path: Path, monkeypatch, caplog, filename: str
) -> None:
    output_dir = tmp_path / "salida"
    csv_path = output_dir / filename
    output_path = output_dir / "grafico.html"
    output_dir.mkdir()
    csv_path.write_text(CSV_CONTENT, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "--csv", str(csv_path), "--output", str(output_path)],
    )

    assert main() == 1
    assert "ruta CSV de salida coincide con el CSV de entrada" in caplog.text
    assert csv_path.read_text(encoding="utf-8") == CSV_CONTENT


def test_main_generates_html_for_valid_output(tmp_path: Path, monkeypatch) -> None:
    csv_path = tmp_path / "ventas.csv"
    output_path = tmp_path / "salida" / "grafico.html"
    csv_path.write_text(CSV_CONTENT, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "--csv", str(csv_path), "--output", str(output_path)],
    )

    assert main() == 0
    assert output_path.is_file()
    assert "plotly.js" in output_path.read_text(encoding="utf-8").lower()

    expected_reports = {
        "ventas_por_region.csv": [
            {"region": "Sur", "total_revenue": "20.00"},
        ],
        "metricas_por_producto.csv": [
            {
                "product_id": "P-1",
                "product_name": "Café",
                "has_name_conflict": "False",
                "units_sold": "2",
                "total_revenue": "20.00",
            },
        ],
        "top_5_clientes.csv": [
            {
                "customer_id": "C-1",
                "customer_name": "Cliente de prueba",
                "has_name_conflict": "False",
                "total_revenue": "20.00",
            },
        ],
    }
    for filename, expected_rows in expected_reports.items():
        report_path = output_path.parent / filename
        assert report_path.is_file()
        with report_path.open(newline="", encoding="utf-8") as report_file:
            assert list(csv.DictReader(report_file)) == expected_rows
