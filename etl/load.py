## importa bibliotecas necessarias
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
import logging
from datetime import date

logger = logging.getLogger(__name__)

## configuracao de conexao
DB_URL = "postgresql+psycopg2://pipeline_user:pipeline_pass@postgres:5432/sales_db"
DB_CONN = {
    "host": "postgres",
    "port": 5432,
    "dbname": "sales_db",
    "user": "pipeline_user",
    "password": "pipeline_pass"
}

def get_engine():
    return create_engine(DB_URL)

def get_conn():
    ## retorna conexao psycopg2
    return psycopg2.connect(**DB_CONN)

## salva dados transformados no PostgreSQL, usa upsert para evitar duplicidade, retorna dict com contagem de registros
def load_sales_data(df_clean: pd.DataFrame, df_metrics: pd.DataFrame) -> dict:
    counts = {}

    ## carrega dados de vendas
    logger.info('Carregando dados de vendas...')

    ## seleciona apenas colunas schema baseado data pedido
    cols = ["order_id", "customer_id", "product_name", "category",
            "quantity", "unit_price", "total_amount", "order_date", "region"]
    df_to_load = df_clean[cols].copy()
    df_to_load["order_date"] = pd.to_datetime(df_to_load["order_date"]).dt.date

    conn = get_conn()
    cur = conn.cursor()

    ## cria tabela temporaria e insere dados via psycopg2
    cur.execute("DROP TABLE IF EXISTS sales_raw_temp")
    cur.execute("""
        CREATE TEMP TABLE sales_raw_temp (
            order_id VARCHAR, customer_id VARCHAR, product_name VARCHAR,
            category VARCHAR, quantity INTEGER, unit_price DECIMAL,
            total_amount DECIMAL, order_date DATE, region VARCHAR
        )
    """)

    ## converte dataframe para lista de tuplas e insere em lote
    rows = [tuple(r) for r in df_to_load.itertuples(index=False)]
    execute_values(cur, "INSERT INTO sales_raw_temp VALUES %s", rows)

    ## Upsert: insere novos registros, ignora duplicatas pelo order_id
    cur.execute("""
        INSERT INTO sales_raw (order_id, customer_id, product_name, category,
                               quantity, unit_price, total_amount, order_date, region)
        SELECT order_id, customer_id, product_name, category,
               quantity, unit_price, total_amount, order_date, region
        FROM sales_raw_temp
        ON CONFLICT (order_id) DO NOTHING
    """)
    counts['sales_raw'] = cur.rowcount
    conn.commit()

    logger.info(f"Vendas: {counts['sales_raw']} novos registros carregados.")

    ## carrega metricas agregadas
    logger.info("Carregando métricas agregadas...")
    metric_cols = ["metric_date", "category", "region", "total_revenue", "total_orders", "avg_order_value"]
    df_m = df_metrics[metric_cols].copy()
    df_m["metric_date"] = pd.to_datetime(df_m["metric_date"]).dt.date
    metric_rows = [tuple(r) for r in df_m.itertuples(index=False)]
    execute_values(cur, """
        INSERT INTO sales_metrics (metric_date, category, region, total_revenue, total_orders, avg_order_value)
        VALUES %s
    """, metric_rows)
    counts['sales_metrics'] = len(metric_rows)
    conn.commit()

    cur.close()
    conn.close()

    logger.info(f"Métricas: {counts['sales_metrics']} registros.")
    return counts

## registra a execucao do pipeline na tabela de log
def log_pipeline_run(counts: dict, status: str, error: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pipeline_log (run_date, records_extracted, records_loaded, status, error_message)
        VALUES (%s, %s, %s, %s, %s)
    """, (date.today(), counts.get("extracted", 0), counts.get("sales_raw", 0), status, error))
    conn.commit()
    cur.close()
    conn.close()
