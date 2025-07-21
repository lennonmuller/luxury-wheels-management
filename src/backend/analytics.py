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

    df_filtrado = df_reservas[df_reservas['status'].isin(['ativa', 'concluída'])].copy()

    if df_filtrado.empty:
        return pd.DataFrame(columns=['mes_ano', 'faturamento'])

    df_filtrado['data_inicio'] = pd.to_datetime(df_filtrado['data_inicio'])

    df_filtrado['mes_ano'] = df_filtrado['data_inicio'].dt.to_period('M')

    faturamento_mensal = df_filtrado.groupby('mes_ano')['valor_total'].sum().reset_index()
    faturamento_mensal.rename(columns={'valor_total': 'faturamento'}, inplace=True)

    return faturamento_mensal.sort_values(by='mes_ano')

def get_veiculos_por_status():
    """Conta quantos veículos existem em cada status dinâmico."""
    df_veiculos = get_veiculos_df()
    if df_veiculos.empty:
        return pd.Series(dtype=int)

    return df_veiculos['status_dinamico'].value_counts()