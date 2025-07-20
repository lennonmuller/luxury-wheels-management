import pandas as pd
from . import database as db


def get_veiculos_df():
    """
    Busca todos os veículos usando a função principal que já calcula o status dinâmico
    e retorna como um DataFrame do Pandas.
    """
    veiculos = db.listar_veiculos()
    if not veiculos:
        logging.warning("get_veiculos_df: Nenhum veículo encontrado.")
        return pd.DataFrame(columns=['id', 'marca', 'modelo', 'status_dinamico'])
    dados_veiculos = [dict(veiculo) for veiculo in veiculos]
    return pd.DataFrame(dados_veiculos)


# Função para obter dados de reservas
def get_reservas_df():
    """Busca todas as reservas e retorna como um DataFrame do Pandas."""
    reservas = db.listar_reservas()
    if not reservas:
        logging.warning("get_reservas_df: Nenhuma reserva encontrada.")
        return pd.DataFrame(columns=['id', 'data_inicio', 'valor_total'])
    dados_reservas = [dict(reserva) for reserva in reservas]
    df = pd.DataFrame(dados_reservas)
    formato_data = '%Y-%m-%d %H:%M:%S'
    df['data_inicio'] = pd.to_datetime(df['data_inicio'], format=formato_data, errors='coerce')
    df['data_fim'] = pd.to_datetime(df['data_fim'], format=formato_data, errors='coerce')

    # Remove linhas que possam ter tido erros de conversão
    df.dropna(subset=['data_inicio', 'data_fim'], inplace=True)

    return df


# --- Funções para os Gráficos ---

def get_faturamento_mensal():
    """Calcula o faturamento total por mês/ano."""

    df_reservas = get_reservas_df()

    if df_reservas.empty:
        return pd.Series(dtype=float)

    df_reservas['mes_ano'] = df_reservas['data_inicio'].dt.to_period('M')
    faturamento = df_reservas.groupby('mes_ano')['valor_total'].sum()
    return faturamento.sort_index()


def get_veiculos_por_status():
    """Conta quantos veículos existem em cada status dinâmico."""
    df_veiculos = get_veiculos_df()
    if df_veiculos.empty:
        return pd.Series(dtype=int)

    return df_veiculos['status_dinamico'].value_counts()