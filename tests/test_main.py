from pathlib import Path

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
