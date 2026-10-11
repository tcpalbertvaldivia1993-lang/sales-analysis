"""Carga y validación de archivos CSV de ventas."""

import logging
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "order_id", "order_date", "customer_id", "customer_name", "region",
    "product_id", "product_name", "category", "quantity", "unit_price",
    "discount_pct",
}
INT64_MAX = 2**63 - 1
UNIT_PRICE_PRECISION = 18
UNIT_PRICE_SCALE = 6
DISCOUNT_PRECISION = 9
DISCOUNT_SCALE = 6
MAX_DECIMAL_REVENUE = Decimal("99999999999999999999999999")


class SalesDataValidationError(ValueError):
    """Error con uno o más problemas encontrados en los datos de ventas."""


def _parse_decimal(value: object) -> Decimal:
    """Convierte un valor a Decimal sin pasar por aritmética binaria."""
    return Decimal(str(value).strip())


def _fits_decimal(value: Decimal, precision: int, scale: int) -> bool:
    """Indica si el valor cabe en un DECIMAL(precision, scale)."""
    if value.is_zero():
        return True
    digits = list(value.as_tuple().digits)
    exponent = value.as_tuple().exponent
    while exponent < 0 and len(digits) > 1 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    fractional_digits = max(0, -exponent)
    integer_digits = max(0, len(digits) + exponent)
    return fractional_digits <= scale and integer_digits <= precision - scale


def validate_sales_data(data: pd.DataFrame) -> pd.DataFrame:
    """Valida columnas, nulos, fechas y valores numéricos; devuelve datos tipados."""
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise SalesDataValidationError(
            "Faltan columnas obligatorias: " + ", ".join(missing)
        )
    if data.empty:
        raise SalesDataValidationError("El CSV no contiene filas de ventas.")

    clean = data.copy().reset_index(drop=True)
    errors: list[str] = []

    for column in sorted(REQUIRED_COLUMNS):
        blank = clean[column].astype("string").str.strip().eq("").fillna(False)
        null = clean[column].isna() | blank
        if null.any():
            rows = (clean.index[null] + 2).tolist()
            errors.append(f"'{column}' tiene valores nulos o vacíos en filas {rows}")

    parsed_dates = pd.to_datetime(clean["order_date"], errors="coerce", format="mixed")
    invalid_dates = parsed_dates.isna()
    if invalid_dates.any():
        rows = (clean.index[invalid_dates] + 2).tolist()
        errors.append(f"'order_date' contiene fechas inválidas en filas {rows}")
    clean["order_date"] = parsed_dates

    parsed: dict[str, list[Decimal | None]] = {}
    for column in ("quantity", "unit_price", "discount_pct"):
        parsed[column] = []
        invalid_rows = []
        non_finite_rows = []
        for row_index, raw_value in enumerate(clean[column]):
            try:
                value = _parse_decimal(raw_value)
            except (InvalidOperation, ValueError):
                parsed[column].append(None)
                invalid_rows.append(row_index + 2)
                continue
            if not value.is_finite():
                parsed[column].append(None)
                non_finite_rows.append(row_index + 2)
                continue
            parsed[column].append(value)
        if invalid_rows:
            errors.append(f"'{column}' contiene valores no numéricos en filas {invalid_rows}")
        if non_finite_rows:
            errors.append(f"'{column}' contiene valores no finitos en filas {non_finite_rows}")

    valid_quantities: list[int | None] = []
    invalid_quantity_rows = []
    for row_index, value in enumerate(parsed["quantity"]):
        if value is None:
            valid_quantities.append(None)
        elif value <= 0 or value != value.to_integral_value() or value > INT64_MAX:
            valid_quantities.append(None)
            invalid_quantity_rows.append(row_index + 2)
        else:
            valid_quantities.append(int(value))
    if invalid_quantity_rows:
        errors.append(
            f"'quantity' debe ser un entero positivo dentro del rango int64 "
            f"(1 a {INT64_MAX}); filas {invalid_quantity_rows}"
        )

    valid_prices: list[Decimal | None] = []
    invalid_price_rows = []
    for row_index, value in enumerate(parsed["unit_price"]):
        if value is None:
            valid_prices.append(None)
        elif (
            value < 0
            or not _fits_decimal(value, UNIT_PRICE_PRECISION, UNIT_PRICE_SCALE)
        ):
            valid_prices.append(None)
            invalid_price_rows.append(row_index + 2)
        else:
            valid_prices.append(value)
    if invalid_price_rows:
        errors.append(
            f"'unit_price' debe ser un importe finito no negativo y caber en DECIMAL(18, 6) "
            f"(máximo 6 decimales); filas {invalid_price_rows}"
        )

    valid_discounts: list[Decimal | None] = []
    invalid_discount_rows = []
    for row_index, value in enumerate(parsed["discount_pct"]):
        if value is None:
            valid_discounts.append(None)
        elif (
            value < 0
            or value > 1
            or not _fits_decimal(value, DISCOUNT_PRECISION, DISCOUNT_SCALE)
        ):
            valid_discounts.append(None)
            invalid_discount_rows.append(row_index + 2)
        else:
            valid_discounts.append(value)
    if invalid_discount_rows:
        errors.append(
            f"'discount_pct' debe estar entre 0 y 1 y caber en DECIMAL(9, 6) "
            f"(máximo 6 decimales); filas {invalid_discount_rows}"
        )

    # DuckDB calcula cada línea y las sumas en DECIMAL(38, 12). Comprobar
    # también el límite del producto y del total evita un desbordamiento SQL.
    if not errors:
        with localcontext() as context:
            context.prec = 50
            total_net_revenue = Decimal(0)
            invalid_revenue_rows = []
            for row_index, (quantity, price, discount) in enumerate(
                zip(valid_quantities, valid_prices, valid_discounts)
            ):
                gross_revenue = Decimal(quantity) * price
                net_revenue = gross_revenue * (Decimal(1) - discount)
                if gross_revenue > MAX_DECIMAL_REVENUE:
                    invalid_revenue_rows.append(row_index + 2)
                total_net_revenue += net_revenue
        if invalid_revenue_rows:
            errors.append(
                "'quantity' y 'unit_price' exceden el rango monetario seguro "
                f"para DuckDB en filas {invalid_revenue_rows}"
            )
        if total_net_revenue > MAX_DECIMAL_REVENUE:
            errors.append("La suma de ingresos excede el rango seguro DECIMAL(38, 12)")

    if errors:
        raise SalesDataValidationError("Errores de validación:\n- " + "\n- ".join(errors))

    clean["quantity"] = pd.Series(valid_quantities, dtype="int64")
    clean["unit_price"] = pd.Series(valid_prices, dtype="object")
    clean["discount_pct"] = pd.Series(valid_discounts, dtype="object")
    logging.getLogger(__name__).info("Validación completada: %d filas", len(clean))
    return clean


def load_and_validate_csv(csv_path: Path) -> pd.DataFrame:
    """Lee un CSV UTF-8 y devuelve sus ventas validadas."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo CSV: {path}")
    try:
        data = pd.read_csv(
            path,
            encoding="utf-8-sig",
            dtype={"quantity": "string", "unit_price": "string", "discount_pct": "string"},
        )
    except pd.errors.EmptyDataError as exc:
        raise SalesDataValidationError(f"El archivo está vacío: {path}") from exc
    return validate_sales_data(data)
