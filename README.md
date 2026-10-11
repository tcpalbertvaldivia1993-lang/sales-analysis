# Análisis de ventas

Proyecto de análisis de ventas con Python, pandas, DuckDB, SQL y Plotly. El CSV incluido contiene datos ficticios de demostración, no datos personales reales.

## Flujo activo

El punto de entrada es `main.py`. Este flujo carga y valida el CSV con pandas, registra los datos en DuckDB, ejecuta las consultas SQL de `sql/duckdb/` y crea un gráfico interactivo con Plotly.

```text
main.py
src/sales_analysis/
  validation.py          # Lectura y validación de CSV con pandas
  duckdb_analysis.py     # Métricas, consultas DuckDB y resultados
  visualization.py      # Gráfico HTML interactivo con Plotly
sql/duckdb/
  summary.sql            # Ingresos, pedidos y ticket promedio
  monthly_sales.sql      # Ingresos mensuales
  top_products.sql       # Ranking agrupado por product_id
data/raw/ventas_demo.csv # CSV ficticio de ejemplo
reports/                 # Gráficos generados, ignorados por Git
tests/                   # Pruebas pytest
```

El ranking agrupa por `product_id`; si un identificador tiene varios nombres, los muestra juntos y marca la inconsistencia.

## Prototipo SQLite conservado

Los siguientes archivos pertenecen a un prototipo separado que no utiliza `main.py`. Se conservan como referencia y no se eliminan:

```text
src/sales_analysis/database.py   # Carga y conexión SQLite
src/sales_analysis/cli.py        # Comandos load/report para SQLite
src/sales_analysis/reporting.py  # Resumen CSV para SQLite
sql/schema.sql                   # Esquema SQLite
sql/queries/                     # Consultas SQL del prototipo SQLite
```

## Requisitos y dependencias

- Python 3.14.4 es la versión usada para verificar este proyecto y corresponde al entorno congelado en `requirements-lock.txt`.
- `requirements.txt` declara los rangos compatibles de las dependencias directas: pandas, DuckDB, Plotly y pytest.
- `requirements-lock.txt` fija las versiones exactas instaladas, incluidas las dependencias transitivas, para reproducir ese entorno.

No se requieren paquetes adicionales para el flujo SQLite, pero sí las dependencias de `requirements.txt` para ejecutar `main.py` y las pruebas.

## Instalación en Windows con VS Code

Abre la carpeta del proyecto en VS Code y usa una terminal PowerShell en la raíz:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
```

Si ya creaste `.venv`, omite el primer comando. Para instalar versiones dentro de los rangos compatibles en vez de las versiones fijadas, usa `python -m pip install -r requirements.txt`.

## Ejecutar el análisis

Con el entorno virtual activado:

```powershell
python main.py
```

Por defecto se usa `data/raw/ventas_demo.csv`. El programa imprime las métricas y guarda el gráfico interactivo en `reports/analisis_ventas_dashboard.html`. La carpeta `reports/` se crea automáticamente si aún no existe. Para visualizarlo, abre `reports/analisis_ventas_dashboard.html` en un navegador.

Para seleccionar otro CSV y una ruta de salida:

```powershell
python main.py --csv "C:\datos\ventas.csv" --output reports\mi_dashboard.html
```

La opción `--output` permite elegir otro destino. La salida debe tener extensión `.html` y no puede apuntar al mismo archivo que el CSV de entrada.

## Ejecutar las pruebas

Desde la raíz del proyecto y con el entorno activado:

```powershell
python -m pytest -v
```

Las pruebas cubren validación de datos, límites numéricos y monetarios, consultas DuckDB, ranking, rutas de salida y generación del HTML.

## Formato del CSV y métricas

El archivo debe contener las columnas `order_id,order_date,customer_id,customer_name,region,product_id,product_name,category,quantity,unit_price,discount_pct`. Cada fila representa una línea de pedido; un pedido puede incluir varias filas.

- `quantity`: entero positivo dentro del rango `int64`.
- `unit_price`: importe no negativo compatible con `DECIMAL(18, 6)`.
- `discount_pct`: proporción entre 0 y 1, compatible con `DECIMAL(9, 6)`; por ejemplo, `0.10` equivale a 10%.
- Las columnas requeridas no pueden estar vacías y `order_date` debe ser una fecha válida.

Los ingresos netos se calculan como cantidad × precio unitario × (1 − descuento). El número de ventas es el número de pedidos distintos y el ticket promedio es el ingreso neto dividido por esos pedidos. No se incluyen impuestos, envío ni devoluciones.
