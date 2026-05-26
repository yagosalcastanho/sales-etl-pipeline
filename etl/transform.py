## importa bibliotecas necessarias
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)
## transforma dados brutos e retorna (df_clean, df_metrics).
def transform_sales_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:

    logger.info(f'Iniciando transformação de {len(df)} registros...')

    df = df.copy()

    ## limpeza 
    df = _clean_data(df)

    ## validacao
    df = _validate_data(df)

    ## enriquecimento
    df = _enrich_data(df)

    ## metricas agregadas
    df_metrics = _calculate_metrics(df)

    logger.info(f'Transformação concluída: {len(df)} registros válidos.')
    return df, df_metrics

## funcao limpeza dados, remove nulo, duplica e padroniza
def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
    initial_count = len(df)

    # remove duplicados 
    df = df.drop_duplicates(subset=["order_id"])

    # remove linhas com campos obrigatorios null 
    df = df.dropna(subset=["order_id", "product_name", "total_amount"])

    # padroniza texto
    df["product_name"] = df["product_name"].str.strip().str.title()
    df["category"]     = df["category"].str.strip().str.lower().str.replace(" ", "_")
    df["region"]       = df["region"].str.strip().str.title()

    # converte tipos
    df["order_date"]   = pd.to_datetime(df["order_date"])
    df["quantity"]     = pd.to_numeric(df["quantity"],    errors="coerce").fillna(0).astype(int)
    df["unit_price"]   = pd.to_numeric(df["unit_price"],  errors="coerce").fillna(0.0)
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0.0)

    removed = initial_count - len(df)
    logger.info(f"Limpeza: {removed} registros removidos.")
    return df

## filtra registros invalidos com regras de negocio
def _validate_data(df: pd.DataFrame) -> pd.DataFrame:
    # Precos e quantidades devem ser positivos
    df = df[df["unit_price"]   > 0]
    df = df[df["total_amount"] > 0]
    df = df[df["quantity"]     > 0]

    # corrige total_amount se divergente (tolerancia 1%)
    expected_total = df["quantity"] * df["unit_price"]
    discrepancy = abs(df["total_amount"] - expected_total) / expected_total
    df.loc[discrepancy > 0.01, "total_amount"] = expected_total[discrepancy > 0.01]

    return df

## Adiciona colunas derivadas
def _enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    df["year"]        = df["order_date"].dt.year
    df["month"]       = df["order_date"].dt.month
    df["month_name"]  = df["order_date"].dt.strftime("%B")
    df["day_of_week"] = df["order_date"].dt.day_name()
    df["is_weekend"]  = df["order_date"].dt.dayofweek >= 5

## segmentacao de valor do pedido
    df["order_segment"] = pd.cut(
        df["total_amount"],
        bins=[0, 50, 200, 500, float("inf")],
        labels=["baixo", "médio", "alto", "premium"]
    )

    return df

## agrega metricas por data, categoria e regiao
def _calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    metrics = (
        df.groupby(["order_date", "category", "region"])
        .agg(
            total_revenue   = ("total_amount", "sum"),
            total_orders    = ("order_id",     "count"),
            avg_order_value = ("total_amount", "mean"),
        )
        .reset_index()
        .rename(columns={"order_date": "metric_date"})
    )
    metrics["total_revenue"]   = metrics["total_revenue"].round(2)
    metrics["avg_order_value"] = metrics["avg_order_value"].round(2)
    return metrics


if __name__ == "__main__":
    from extract import extract_sales_data
    df_raw = extract_sales_data(50)
    df_clean, df_metrics = transform_sales_data(df_raw)
    print("── Dados limpos ──")
    print(df_clean.head())
    print("\n── Métricas ──")
    print(df_metrics.head())