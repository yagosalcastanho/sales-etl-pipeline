-- TABELA VENDAS (RAW DATA)

-- 	TABELAS BRUTAS ORDENADAS PELO ID
CREATE TABLE IF NOT EXISTS sales_raw (
    id              SERIAL PRIMARY KEY,
    order_id        VARCHAR(50) UNIQUE NOT NULL,
    customer_id     VARCHAR(50),
    product_name    VARCHAR(200),
    category        VARCHAR(100),
    quantity        INTEGER,
    unit_price      DECIMAL(10, 2),
    total_amount    DECIMAL(10, 2),
    order_date      DATE,
    region          VARCHAR(100),
    loaded_at       TIMESTAMP DEFAULT NOW()
);


-- TABELA METRICAS CRIADAS PARA CATEGORIA, REGIAO, PEDIDOS E TICKET MEDIO

CREATE TABLE IF NOT EXISTS sales_metrics (
    id              SERIAL PRIMARY KEY,
    metric_date     DATE,
    category        VARCHAR(100),
    region          VARCHAR(100),
    total_revenue   DECIMAL(12, 2),
    total_orders    INTEGER,
    avg_order_value DECIMAL(10, 2),
    calculated_at   TIMESTAMP DEFAULT NOW()
);


-- LOG PIPELINE


CREATE TABLE IF NOT EXISTS pipeline_log (
    id                  SERIAL PRIMARY KEY,
    run_date            DATE,
    records_extracted   INTEGER,
    records_loaded      INTEGER,
    status              VARCHAR(20),
    error_message       TEXT,
    executed_at         TIMESTAMP DEFAULT NOW()
);
