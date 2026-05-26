## importa as bibiliotecas e funcoes necessarias
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import logging
from pathlib import Path
from typing import Optional

## URL de conexao com banco de dados
DB_URL = "postgresql+psycopg2://pipeline_user:pipeline_pass@postgres:5432/sales_db"
DB_CONN = {
    "host": "postgres",
    "port": 5432,
    "dbname": "sales_db",
    "user": "pipeline_user",
    "password": "pipeline_pass"
}

## gera relatotios em imagem (PNG) a partir dados vendas do banco
class SalesReportGenerator:

    ## incializa classe com URL
    def __init__(self, db_url: str, output_dir: Optional[Path] = None):
        self.db_url = db_url
        self.output_dir = output_dir or Path("/opt/airflow/reports")
        self.logger = self._setup_logger()
        self._setup_visual_style()

    ## configura logger (monitora e depura)
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    ## estilo visual dos graficos
    def _setup_visual_style(self):
        sns.set_theme(style="whitegrid", palette="muted")

    ## gera o relatorio completo, salva e retorna arquivo
    def generate_report(self) -> Path:
        self.logger.info("Iniciando geração do relatório de vendas...")
        try:
            df = self._load_data()
            df = self._prepare_data(df)
            if df.empty:
                self.logger.warning("DataFrame vazio. Relatório não gerado.")
                return None
            self.output_dir.mkdir(parents=True, exist_ok=True)
            fig = self._create_figure(df)
            output_path = self._save_report(fig)
            self.logger.info(f"Relatório gerado com sucesso: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Erro durante geração do relatório: {e}", exc_info=True)
            raise

    ## carrega dados do banco via psycopg2, retorna DataFrame
    def _load_data(self) -> pd.DataFrame:
        try:
            conn = psycopg2.connect(**DB_CONN)
            df = pd.read_sql("SELECT * FROM sales_raw", conn)
            conn.close()
            return df
        except Exception as e:
            self.logger.error(f"Erro de conexão com banco: {e}")
            raise

    ## prepara dados para analise convertendo datas e criando colunas derivadas
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["order_date"] = pd.to_datetime(df["order_date"], errors='coerce')
        df["month"] = df["order_date"].dt.to_period("M").astype(str)
        return df

    ## cria os 4 graficos e retorna figura completa
    def _create_figure(self, df: pd.DataFrame):
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("Relatório de Vendas — Pipeline ETL",
                     fontsize=16, fontweight="bold")
        self._plot_revenue_by_month(df, axes[0, 0])
        self._plot_top_categories(df, axes[0, 1])
        self._plot_region_distribution(df, axes[1, 0])
        self._plot_avg_ticket_by_segment(df, axes[1, 1])
        plt.tight_layout()
        return fig

    ## gera grafico de receita mes
    def _plot_revenue_by_month(self, df: pd.DataFrame, ax):
        monthly = df.groupby("month")["total_amount"].sum().reset_index()
        ax.bar(monthly["month"], monthly["total_amount"], color="#4C72B0")
        ax.set_title("Receita por Mês")
        ax.set_xlabel("Mês")
        ax.set_ylabel("Receita (R$)")
        ax.tick_params(axis="x", rotation=45)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R${x:,.0f}"))

    ## gera grafico top categorias receita
    def _plot_top_categories(self, df: pd.DataFrame, ax):
        top_cats = (df.groupby("category")["total_amount"]
                    .sum().nlargest(5).reset_index())
        ax.barh(top_cats["category"], top_cats["total_amount"], color="#55A868")
        ax.set_title("Top 5 Categorias por Receita")
        ax.set_xlabel("Receita Total (R$)")

    ## gera grafico distribuicao pedidos regiao
    def _plot_region_distribution(self, df: pd.DataFrame, ax):
        region_counts = df["region"].value_counts()
        ax.pie(region_counts, labels=region_counts.index,
               autopct="%1.1f%%", startangle=90,
               colors=sns.color_palette("pastel"))
        ax.set_title("Pedidos por Região")

    ## gera grafico ticket medio segmento
    def _plot_avg_ticket_by_segment(self, df: pd.DataFrame, ax):
        segment_avg = df.groupby("region")["total_amount"].mean().reset_index()
        ax.bar(segment_avg["region"].astype(str),
               segment_avg["total_amount"], color="#C44E52")
        ax.set_title("Ticket Médio por Segmento")
        ax.set_xlabel("Segmento")
        ax.set_ylabel("Valor Médio (R$)")

    ## salva figura como PNG e retorna caminho do arquivo
    def _save_report(self, fig) -> Path:
        output_path = self.output_dir / "sales_report.png"
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path


## funcao wrapper para compatibilidade com a DAG do Airflow
def generate_report():
    generator = SalesReportGenerator(db_url=DB_URL)
    return str(generator.generate_report())


## teste local
if __name__ == "__main__":
    path = generate_report()
    print(f"Relatorio gerado: {path}")
