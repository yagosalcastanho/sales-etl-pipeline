## importa bibliotecas necessarias
import requests
import pandas as pd
import logging
from datetime import datetime

## config basica para logging, ajuda a monitorar processo extracao e identificar erros.
logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)

## funcao extrair dados api
def extract_sales_data(limit: int =100) -> pd.DataFrame:
    '''
    busca dados de pedidos API DummyJSON
    retorna dataframe dados brutos
    '''
    logger.info(f'Inciando extração de dados {limit} pedidos...')

    url = f'https://dummyjson.com/carts?limit={limit}&skip=0'
    
## pega o url e trata erros de conexão
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f'Erro na API: {e}')
        raise

    carts = data.get('carts', [])
    rows = []

## define estrutura dos dados de cada produto em cada pedido de acordo com primarykey order_id e customer_id
    for cart in carts:
        for product in cart.get('products', []):
            rows.append({
                'order_id':     f"ORD-{cart['id']:04d}-{product['id']:04d}",
                'customer_id':  f"CUST-{cart['userId']:04d}",
                'product_name':   product.get('title', ''),
                'category':       product.get('category', 'sem_categoria'),
                'quantity':       product.get('quantity', 0),
                'unit_price':     product.get('price', 0.0),
                'total_amount':   product.get('total', 0.0),
                ## Simulando datas nos ultimos 90 dias
                'order_date':     _simulate_date(cart['id']),
                'region':         _assign_region(cart['userId']),
            })

            ## simulate_date e assign_region  
    
    df = pd.DataFrame(rows)
    logger.info(f'Extração concluída: {len(df)} registros obtidos.')
    return df

## funcao gera data simulada de acordo com o id do carrinho para criar variabilidade nos dados
def _simulate_date(cart_id: int) -> str:
    from datetime import timedelta
    base = datetime(2026, 1, 1)
    offset = (cart_id * 3) % 90  # variabilidade de ate 90 dias
    return (base + timedelta(days=offset)).strftime('%Y-%m-%d')

## atribui regiao com base userid
def _assign_region(user_id: int) -> str:
    regions = ['Norte','Sul', 'Leste', 'Oeste', 'Centro']
    return regions[user_id % len(regions)]

if __name__ == "__main__":
    df = extract_sales_data(limit=50)
    print(df.head())
    print(f'\nShape: {df.shape}')
    print(f'\nColunas: {df.dtypes}')
