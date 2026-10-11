"""Conexión y carga de datos de ventas a SQLite."""

import csv
import sqlite3
from datetime import date
from pathlib import Path

REQUIRED_COLUMNS = {
    "order_id", "order_date", "customer_id", "customer_name", "region",
    "product_id", "product_name", "category", "quantity", "unit_price",
    "discount_pct",
}


def connect(db_path: Path) -> sqlite3.Connection:
    """Abre la base y activa las claves foráneas."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection, schema_path: Path) -> None:
    """Crea las tablas e índices declarados en el esquema SQL."""
    connection.executescript(schema_path.read_text(encoding="utf-8"))


def load_csv(connection: sqlite3.Connection, csv_path: Path) -> int:
    """Valida y carga un CSV. Una carga repetida reemplaza el conjunto anterior."""
    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Faltan columnas requeridas: {', '.join(sorted(missing))}")

        records = []
        for line_number, row in enumerate(reader, start=2):
            try:
                order_date = date.fromisoformat(row["order_date"]).isoformat()
                quantity = int(row["quantity"])
                unit_price = float(row["unit_price"])
                discount_pct = float(row["discount_pct"] or 0)
                text_fields = [row[name].strip() for name in (
                    "order_id", "customer_id", "customer_name", "region",
                    "product_id", "product_name", "category",
                )]
                if any(not value for value in text_fields):
                    raise ValueError("los campos de texto no pueden estar vacíos")
                if quantity <= 0:
                    raise ValueError("quantity debe ser mayor que cero")
                if unit_price < 0:
                    raise ValueError("unit_price no puede ser negativo")
                if not 0 <= discount_pct <= 1:
                    raise ValueError("discount_pct debe estar entre 0 y 1")
                records.append((
                    *text_fields[:1], order_date, *text_fields[1:], quantity,
                    unit_price, discount_pct,
                ))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Fila {line_number}: {exc}") from exc

    with connection:
        connection.execute("DELETE FROM sales")
        connection.executemany(
            """INSERT INTO sales (
                order_id, order_date, customer_id, customer_name, region,
                product_id, product_name, category, quantity, unit_price, discount_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            records,
        )
    return len(records)
