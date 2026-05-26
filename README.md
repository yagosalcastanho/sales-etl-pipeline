# Sales ETL Pipeline

<div align="center">

**[Português](#português) • [English](#english)**

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8.1-017CEE?style=flat-square&logo=apacheairflow)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![Pandas](https://img.shields.io/badge/Pandas-2.2-150458?style=flat-square&logo=pandas)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## português

Pipeline ETL automatizado de ponta a ponta para análise de dados de vendas, desenvolvido no VSCode em ambiente Linux. O sistema coleta dados de uma API externa, realiza limpeza e transformação com Pandas, persiste em PostgreSQL via psycopg2 e gera relatórios analíticos em PNG — tudo orquestrado pelo Apache Airflow em containers Docker.

### Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                  Apache Airflow (DAG diário 06:00)          │
│                                                             │
│  ┌─────────┐    ┌───────────┐    ┌──────┐    ┌──────────┐  │
│  │ Extract │ →  │ Transform │ →  │ Load │ →  │  Report  │  │
│  │  API    │    │  Pandas   │    │  PG  │    │  Charts  │  │
│  └─────────┘    └───────────┘    └──────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                               │
         ▼                               ▼
  DummyJSON API                   PostgreSQL 15
  (dados de e-commerce)      ┌─────────────────────┐
                             │ • sales_raw          │
                             │ • sales_metrics      │
                             │ • pipeline_log       │
                             └─────────────────────┘
```

### tecnologias

| Camada | Tecnologia | Uso |
|---|---|---|
| Orquestração | Apache Airflow 2.8.1 | Agendamento e monitoramento do pipeline |
| Transformação | Python 3.11 + Pandas | Limpeza, validação e enriquecimento dos dados |
| Banco de dados | PostgreSQL 15 | Armazenamento persistente via psycopg2 |
| Infraestrutura | Docker + Docker Compose | Ambiente reproduzível e isolado |
| Visualização | Matplotlib + Seaborn | Relatório PNG com 4 gráficos analíticos |
| Fonte de dados | DummyJSON API | API pública de e-commerce, sem autenticação |

### estrutura do projeto

```
sales_pipeline/
├── dags/
│   └── sales_etl_dag.py        # DAG do Airflow com 4 tasks encadeadas
├── etl/
│   ├── extract.py              # Coleta dados da API REST
│   ├── transform.py            # Limpeza, validação e enriquecimento
│   └── load.py                 # Upsert no PostgreSQL via psycopg2
├── analysis/
│   └── report.py               # Geração de relatório com 4 gráficos
├── sql/
│   └── create_tables.sql       # Schema: sales_raw, sales_metrics, pipeline_log
├── reports/                    # PNGs gerados automaticamente pelo pipeline
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### quickstart

**Pré-requisitos:** Docker e Docker Compose instalados. Portas `8080` e `5433` livres.

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/sales-etl-pipeline.git
cd sales-etl-pipeline

# 2. Sobe todos os containers
docker compose up -d

# 3. Aguarda ~30s e acessa o Airflow
open http://localhost:8080
```

credenciais do airflow: `admin` / `admin`

Para executar o pipeline manualmente: acesse `http://localhost:8080`, localize a DAG `sales_etl_pipeline`, ative o toggle e clique em Trigger DAG. Acompanhe as tasks: `extract → transform → load → report`.

### O que o pipeline faz

**Extract** — Conecta na [DummyJSON API](https://dummyjson.com/carts) e coleta dados de carrinhos de compra simulando pedidos reais de e-commerce. Os dados são serializados via XCom para a próxima task.

**Transform** — Aplica três camadas de processamento: limpeza (remove duplicatas, trata nulos, padroniza tipos), validação (filtra registros inválidos, corrige divergências de valor com tolerância de 1%) e enriquecimento (adiciona `month`, `day_of_week`, `is_weekend` e `order_segment`).

**Load** — Insere os dados no PostgreSQL via psycopg2 usando upsert (`INSERT ... ON CONFLICT DO NOTHING`), garantindo idempotência em re-execuções. Cada run é registrado na tabela `pipeline_log`.

**Report** — Gera um relatório PNG com 4 gráficos: receita por mês, top 5 categorias por receita, distribuição de pedidos por região e ticket médio por região.

### Schema do Banco

```sql
sales_raw       -- registros brutos de vendas (order_id UNIQUE)
sales_metrics   -- métricas agregadas por data, categoria e região
pipeline_log    -- histórico de execuções com status e contagens
```

### consultas uteis

```bash
docker exec -it postgres_sales psql -U pipeline_user -d sales_db
```

```sql
-- Total de registros carregados
SELECT COUNT(*) FROM sales_raw;

-- Receita por região
SELECT region, SUM(total_amount) AS receita
FROM sales_raw
GROUP BY region
ORDER BY receita DESC;

-- Histórico de execuções do pipeline
SELECT run_date, records_loaded, status, executed_at
FROM pipeline_log
ORDER BY executed_at DESC;
```

### configuração

O agendamento padrão é `0 6 * * *` (todo dia às 06:00). Para alterar, edite `schedule_interval` em `dags/sales_etl_dag.py`. Para produção, mova as credenciais do `docker-compose.yml` para um arquivo `.env` e ajuste as referências.

---

## english

A fully automated end-to-end ETL pipeline for sales data analysis, built in VSCode on Linux. The system fetches data from an external API, cleans and transforms it with Pandas, persists to PostgreSQL via psycopg2, and generates analytical PNG reports — all orchestrated by Apache Airflow running in Docker containers.

### architecture

```
┌─────────────────────────────────────────────────────────────┐
│               Apache Airflow (Daily DAG at 06:00)           │
│                                                             │
│  ┌─────────┐    ┌───────────┐    ┌──────┐    ┌──────────┐  │
│  │ Extract │ →  │ Transform │ →  │ Load │ →  │  Report  │  │
│  │  API    │    │  Pandas   │    │  PG  │    │  Charts  │  │
│  └─────────┘    └───────────┘    └──────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                               │
         ▼                               ▼
  DummyJSON API                   PostgreSQL 15
  (e-commerce data)          ┌─────────────────────┐
                             │ • sales_raw          │
                             │ • sales_metrics      │
                             │ • pipeline_log       │
                             └─────────────────────┘
```

### tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Orchestration | Apache Airflow 2.8.1 | Pipeline scheduling and monitoring |
| Transformation | Python 3.11 + Pandas | Data cleaning, validation and enrichment |
| Database | PostgreSQL 15 | Persistent storage via psycopg2 |
| Infrastructure | Docker + Docker Compose | Reproducible and isolated environment |
| Visualization | Matplotlib + Seaborn | PNG report with 4 analytical charts |
| Data source | DummyJSON API | Public e-commerce API, no auth required |

### project structure

```
sales_pipeline/
├── dags/
│   └── sales_etl_dag.py        # Airflow DAG with 4 chained tasks
├── etl/
│   ├── extract.py              # Fetches data from REST API
│   ├── transform.py            # Cleaning, validation and enrichment
│   └── load.py                 # Upsert to PostgreSQL via psycopg2
├── analysis/
│   └── report.py               # Generates report with 4 charts
├── sql/
│   └── create_tables.sql       # Schema: sales_raw, sales_metrics, pipeline_log
├── reports/                    # Auto-generated PNGs
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### quickstart

**Prerequisites:** Docker and Docker Compose installed. Ports `8080` and `5433` must be free.

```bash
# 1. Clone the repository
git clone https://github.com/your-username/sales-etl-pipeline.git
cd sales-etl-pipeline

# 2. Start all containers
docker compose up -d

# 3. Wait ~30s and open Airflow
open http://localhost:8080
```

Airflow credentials: `admin` / `admin`

To trigger the pipeline manually: go to `http://localhost:8080`, find the `sales_etl_pipeline` DAG, enable the toggle and click Trigger DAG. Watch the tasks run: `extract → transform → load → report`.

### what the pipeline does

**Extract** — Connects to the [DummyJSON API](https://dummyjson.com/carts) and fetches shopping cart data simulating real e-commerce orders. Data is serialized via XCom to the next task.

**Transform** — Applies three processing layers: cleaning (removes duplicates, handles nulls, standardizes types), validation (filters invalid records, corrects value discrepancies with 1% tolerance) and enrichment (adds `month`, `day_of_week`, `is_weekend` and `order_segment`).

**Load** — Inserts data into PostgreSQL via psycopg2 using upsert (`INSERT ... ON CONFLICT DO NOTHING`), ensuring idempotency across re-runs. Each execution is logged to the `pipeline_log` table.

**Report** — Generates a PNG report with 4 charts: revenue by month, top 5 categories by revenue, order distribution by region, and average ticket by region.

### database schema

```sql
sales_raw       -- raw sales records (order_id UNIQUE)
sales_metrics   -- metrics aggregated by date, category and region
pipeline_log    -- execution history with status and record counts
```

### useful queries

```bash
docker exec -it postgres_sales psql -U pipeline_user -d sales_db
```

```sql
-- Total records loaded
SELECT COUNT(*) FROM sales_raw;

-- Revenue by region
SELECT region, SUM(total_amount) AS revenue
FROM sales_raw
GROUP BY region
ORDER BY revenue DESC;

-- Pipeline execution history
SELECT run_date, records_loaded, status, executed_at
FROM pipeline_log
ORDER BY executed_at DESC;
```

### configuration

The default schedule is `0 6 * * *` (every day at 06:00 AM). To change it, edit `schedule_interval` in `dags/sales_etl_dag.py`. For production, move credentials from `docker-compose.yml` to a `.env` file and update the references accordingly.

---

### contributing | contribuindo

Contributions are more than welcome. Fork the project, create a branch, commit your changes and open a pull request, maybe you know something that i don´t know :).
Contribuições são mais que bem-vindas. Faça um fork, crie uma branch, commite suas alterações e abra um pull request, talvez você saiba de algo que eu não sei.

### License | Licença

Distributed under the MIT License.
Distribuído sob a licença MIT.

---

<div align="center">
  Developed as part of a Data Engineering portfolio project<br>
  Desenvolvido como parte de um projeto de portfólio de Engenharia de Dados
</div>
