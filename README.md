# Análisis de ventas con Python y SQL

Proyecto de portafolio que procesa un archivo CSV de ventas, valida sus datos y genera métricas y agrupaciones con Python, pandas y DuckDB. También exporta un gráfico interactivo de ingresos netos mensuales como archivo HTML.

## Objetivo

El proyecto muestra un flujo de análisis desde un CSV hasta resultados resumidos: validar los datos de entrada, calcular métricas de ventas y explorar resultados por región, producto y cliente.

## Tecnologías

- **Python:** punto de entrada, validación y coordinación del análisis.
- **pandas:** lectura y validación tabular de datos, y análisis exploratorio.
- **DuckDB:** ejecución de consultas analíticas sobre los datos cargados en memoria.
- **SQL:** definición de las consultas de resumen, ventas mensuales y ranking de productos.
- **Plotly:** generación del gráfico interactivo en HTML.
- **pytest:** pruebas de validación, cálculos, consultas y salida HTML.

Las dependencias directas están declaradas en `requirements.txt`; `requirements-lock.txt` contiene versiones fijadas para reproducir el entorno congelado del proyecto.

El código requiere Python 3.10 o superior por la sintaxis de anotaciones de tipos utilizada. Para instalar las versiones exactas de `requirements-lock.txt`, se requiere Python 3.11 o superior. El entorno fijado se verificó con Python 3.14.4, pero esa versión concreta no es obligatoria.

## Funcionalidades

El flujo principal se ejecuta desde `main.py` y:

1. Lee un CSV y valida sus columnas, fechas, cantidades, precios y descuentos.
2. Calcula los ingresos netos, el número de pedidos y el ticket promedio.
3. Agrupa ingresos por región y por producto, y presenta los cinco clientes con mayor gasto neto.
4. Calcula ventas por mes y genera un ranking de productos por unidades e ingresos.
5. Exporta un gráfico interactivo de ingresos netos mensuales.
6. Exporta a CSV los ingresos por región, las métricas por producto y los cinco clientes con mayor gasto neto.

El ranking agrupa por `product_id`. Si un mismo identificador aparece con varios nombres, los presenta juntos y marca la inconsistencia.

## Estructura del proyecto

```text
.
├── main.py
├── requirements.txt
├── requirements-lock.txt
├── data/
│   ├── raw/                  # CSV de entrada local; no se distribuye en el repositorio
│   └── processed/            # reservado para datos procesados
├── reports/                  # destino de los informes HTML y CSV generados
├── sql/
│   ├── duckdb/               # consultas del flujo principal
│   ├── queries/              # consultas del prototipo SQLite
│   └── schema.sql            # esquema del prototipo SQLite
├── src/sales_analysis/
│   ├── validation.py         # lectura y validación del CSV
│   ├── exploratory.py        # agrupaciones con pandas
│   ├── exporting.py          # exportación de resultados exploratorios a CSV
│   ├── duckdb_analysis.py    # métricas y consultas DuckDB
│   ├── visualization.py      # gráfico HTML con Plotly
│   ├── database.py           # conexión y carga para el prototipo SQLite
│   ├── cli.py                # comandos del prototipo SQLite
│   └── reporting.py          # resumen CSV del prototipo SQLite
└── tests/
    ├── test_main.py
    ├── test_sales_analysis.py
    └── test_exploratory.py
```

Los módulos SQLite se conservan como prototipo separado. No forman parte del flujo ejecutado por `main.py`.

## Requisitos e instalación

Se recomienda Python 3.11 o superior. `requirements-lock.txt` fija pandas 3.0.6, que requiere como mínimo Python 3.11. `requirements.txt` declara rangos de dependencias, no una versión concreta de Python.

### Windows (PowerShell)

Desde la carpeta raíz del proyecto:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
```

Si ya existe el entorno virtual, omite la primera línea. Para instalar versiones dentro de los rangos declarados en lugar de las versiones fijadas, puedes usar:

```powershell
python -m pip install -r requirements.txt
```

### Linux o WSL

Desde la carpeta raíz del proyecto:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

También puedes instalar con los rangos de `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

## Ejecutar el análisis

El programa espera un CSV con las columnas requeridas. El repositorio no distribuye `data/raw/ventas_demo.csv`, así que indica la ruta a un CSV disponible localmente.

En Windows:

```powershell
python main.py --csv "C:\ruta\ventas.csv"
```

En Linux o WSL:

```bash
python main.py --csv "/ruta/ventas.csv"
```

Si el CSV está en `data/raw/ventas_demo.csv`, también puedes ejecutar `python main.py` sin indicar `--csv`. Si ese archivo predeterminado no existe, el programa registra un error indicando que no encontró el CSV y termina con código 1. No descarga ni crea datos automáticamente.

El destino predeterminado del gráfico es:

```text
reports/analisis_ventas_dashboard.html
```

La carpeta `reports/` se crea si no existe. Puedes cambiar el destino con `--output`, siempre que termine en `.html` y no coincida con la ruta del CSV.
El programa guarda también estos tres archivos CSV en el mismo directorio que el HTML:

- `ventas_por_region.csv`: ingresos netos agrupados por región.
- `metricas_por_producto.csv`: nombres, unidades vendidas e ingresos netos por producto, con una marca de conflictos de nombres.
- `top_5_clientes.csv`: hasta cinco clientes con mayor gasto neto.

Si `--output` apunta a otro directorio, los CSV se guardan junto al HTML en ese directorio.

En Windows:

```powershell
python main.py --csv "C:\ruta\ventas.csv" --output "reports\mi_dashboard.html"
```

En Linux o WSL:

```bash
python main.py --csv "/ruta/ventas.csv" --output "reports/mi_dashboard.html"
```

Para abrir el gráfico, abre el HTML generado en un navegador. En PowerShell puedes usar:

```powershell
Start-Process .\reports\analisis_ventas_dashboard.html
```

En Linux:

```bash
xdg-open reports/analisis_ventas_dashboard.html
```

En WSL con integración de Windows:

```bash
explorer.exe "$(wslpath -w reports/analisis_ventas_dashboard.html)"
```

## Ejecutar las pruebas

Con el entorno virtual activado y desde la raíz del proyecto:

```bash
python -m pytest -v
```

Las pruebas comprueban la validación de datos y límites numéricos, las métricas y agrupaciones, las consultas y el ranking de DuckDB, y las condiciones de salida, generación del HTML y exportación de los CSV.

## Resultados y dashboard

Al terminar, el programa imprime en la terminal métricas generales, ingresos por región y producto, los cinco clientes con mayor gasto y el ranking de productos. También guarda un gráfico de líneas interactivo con los ingresos netos por mes y tres tablas CSV con los principales resultados exploratorios.

El dashboard contiene ese gráfico mensual; no es un panel con filtros ni incluye las tablas impresas en la terminal. El HTML y los CSV se generan localmente dentro de `reports/` (o junto al HTML si se indica otro destino) y no se incluyen en el repositorio. No se presentan cifras ni capturas en este README.

## Formato de entrada

Cada fila representa una línea de pedido. Un pedido puede aparecer en varias filas. El CSV debe incluir:

```text
order_id,order_date,customer_id,customer_name,region,product_id,product_name,category,quantity,unit_price,discount_pct
```

Las cantidades deben ser enteros positivos; los precios, importes no negativos; y el descuento, una proporción entre `0` y `1` (por ejemplo, `0.10` equivale a 10 %). Las fechas deben ser válidas y las columnas requeridas no pueden estar vacías.

Los ingresos netos se calculan como cantidad × precio unitario × (1 − descuento). El análisis no incluye impuestos, envío ni devoluciones.

## Limitaciones y mejoras futuras

- El análisis depende de que el CSV tenga las columnas y los tipos de datos esperados.
- El gráfico actual muestra ingresos mensuales y no permite filtrar ni explorar los grupos desde el navegador.
- No se modelan impuestos, envío, devoluciones ni otros ajustes contables.
- Los módulos SQLite son un prototipo independiente y no están integrados en el flujo principal.

Como mejoras futuras se podrían incorporar filtros al dashboard, comparar periodos y categorías, y ampliar el conjunto de casos de prueba con más archivos de entrada.

## Datos de demostración

Los datos de demostración son ilustrativos y no deben considerarse datos reales ni representar resultados de un negocio. El CSV local `data/raw/ventas_demo.csv` no se distribuye en este repositorio.
