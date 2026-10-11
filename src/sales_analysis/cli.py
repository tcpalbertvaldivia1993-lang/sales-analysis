"""Interfaz de línea de comandos del proyecto."""

import argparse
from pathlib import Path

from .database import connect, initialize, load_csv
from .reporting import write_summary

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data/processed/ventas.db"
SCHEMA = ROOT / "sql/schema.sql"


def main() -> None:
    parser = argparse.ArgumentParser(description="Análisis de ventas con Python y SQLite")
    commands = parser.add_subparsers(dest="command", required=True)

    load_parser = commands.add_parser("load", help="Cargar ventas desde un CSV")
    load_parser.add_argument("--csv", type=Path, required=True, help="Ruta al CSV de ventas")
    load_parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Ruta de la base SQLite")

    report_parser = commands.add_parser("report", help="Generar resumen ejecutivo en CSV")
    report_parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Ruta de la base SQLite")
    report_parser.add_argument(
        "--output", type=Path, default=ROOT / "reports/resumen_ventas.csv",
        help="Ruta de salida del resumen",
    )

    args = parser.parse_args()
    if args.command == "load":
        with connect(args.db) as connection:
            initialize(connection, SCHEMA)
            count = load_csv(connection, args.csv)
        print(f"Carga completada: {count} líneas en {args.db}")
    elif args.command == "report":
        if not args.db.exists():
            parser.error(f"No existe la base {args.db}. Ejecuta primero el comando load.")
        with connect(args.db) as connection:
            metrics = write_summary(connection, args.output)
        print("Resumen de ventas")
        for name, value in metrics.items():
            print(f"{name}: {value}")
        print(f"Informe guardado en {args.output}")


if __name__ == "__main__":
    main()
