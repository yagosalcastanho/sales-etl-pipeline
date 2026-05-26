## importa bibliotecas necessarias
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from io import StringIO
import sys

sys.path.insert(0, "/opt/airflow")

from etl.extract   import extract_sales_data
from etl.transform import transform_sales_data
from etl.load      import load_sales_data, log_pipeline_run
from analysis.report import generate_report

default_args = {
    "owner":            "data_engineer",
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
}

## funcao extrai dados da API, serializa para o XCom (comunicacao entre tasks)
def task_extract(**context):
    df = extract_sales_data(limit=100)
    context["ti"].xcom_push(key="raw_data", value=df.to_json())
    return f"Extraídos {len(df)} registros"
## funcao transforma dados brutos e serializa para Xcom
def task_transform(**context):
    import pandas as pd
    raw_json = context["ti"].xcom_pull(key="raw_data", task_ids="extract")
    df_raw   = pd.read_json(StringIO(raw_json))

    df_clean, df_metrics = transform_sales_data(df_raw)

    context["ti"].xcom_push(key="clean_data",   value=df_clean.to_json())
    context["ti"].xcom_push(key="metrics_data", value=df_metrics.to_json())
    return f"Transformados {len(df_clean)} registros válidos"

## funcao carrega tarefa para banco registra no log
def task_load(**context):
    import pandas as pd
    ti = context["ti"]
    df_clean   = pd.read_json(StringIO(ti.xcom_pull(key="clean_data",   task_ids="transform")))
    df_metrics = pd.read_json(StringIO(ti.xcom_pull(key="metrics_data", task_ids="transform")))

    counts = load_sales_data(df_clean, df_metrics)
    counts["extracted"] = len(df_clean)
    log_pipeline_run(counts, status="success")
    return f"Carregados {counts['sales_raw']} novos registros"

## funcao gera relatorio e salva como PNG
def task_report(**context):
    path = generate_report()
    return f"Relatório gerado: {path}"


with DAG(
    dag_id="sales_etl_pipeline",
    default_args=default_args,
    description="Pipeline ETL completo de análise de vendas",
    schedule_interval="0 6 * * *",    # todo dia as 06:00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["etl", "sales", "portfolio"],
) as dag:

    extract   = PythonOperator(task_id="extract",   python_callable=task_extract)
    transform = PythonOperator(task_id="transform", python_callable=task_transform)
    load      = PythonOperator(task_id="load",      python_callable=task_load)
    report    = PythonOperator(task_id="report",    python_callable=task_report)

    # define ordem execucao
    extract >> transform >> load >> report
