import pandas as pd
from . import database as db

def get_veiculos_df():
    """Busca todos os veiculos e retorna como um DataFrame do Pandas"""
    veiculos = db.listar_veiculos()
    if not veiculos:
        return pd.DataFrame() #Retorna DF vazio se nao houver dados
    return pd.DataFrame(veiculos, columns=['id', 'marca', 'modelo', 'ano', 'placa', 'cor', 'valor_diaria', 'status', 'data_proxima_revisao', 'imagem_path'])

def get_reservas_df():
    """Busca todas as reservas e retorna como um DataFrame do Pandas"""
    reservas = db.listar_reservas()
    if not reservas:
        return pd.DataFrame()
    df = pd.DataFrame(reservas, columns=['id', 'id_cliente', 'id_veiculo', 'id_forma_pagamento', 'data_inicio', 'data_fim', 'valor_total', 'status'])
    #convertendo colunas de data para o tipo datetime do pandas para calculos
    df['data_inicio'] = pd.to_datetime(df['data_inicio'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['data_fim'] = pd.to_datetime(df['data_fim'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    return df

# Funções para os gráficos

def get_faturamento_mensal():
    """Calcula a faturamento mensal por mês/ano"""
    df_reservas = get_reservas_df()
    if df_reservas.empty:
        return pd.Series(dtype=float)

    #data de inicio para contabilizar o faturamento
    df_reservas['mes_ano'] = df_reservas['data_inicio'].dt.to_period('M')

    faturamento = df_reservas.groupby('mes_ano')['valor_total'].sum()
    return faturamento.sort_index()

def get_veiculos_por_status():
    """ Conta quantos veículos existem em cada status."""
    df_veiculos = get_veiculos_df()
    if df_veiculos.empty:
        return pd.Series(dtype=int)

    return df_veiculos['status'].value_counts()
