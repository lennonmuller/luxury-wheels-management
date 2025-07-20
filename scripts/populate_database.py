# scripts/populate_database.py

import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta
import os
import sys
import logging

# Adiciona a pasta 'src' ao path para que possamos importar 'database'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from backend import database as db
from faker.exceptions import UniquenessException

# Configuração básica do logging para o script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Faker para Portugal
fake = Faker('pt_PT')


def limpar_tabelas(conn):
    """Limpa todos os dados das tabelas para começar do zero."""
    cursor = conn.cursor()
    logging.info("Limpando tabelas existentes...")
    # A ordem é importante devido às chaves estrangeiras (reservas depende de clientes/veiculos)
    cursor.execute("DELETE FROM reservas;")
    cursor.execute("DELETE FROM veiculos;")
    cursor.execute("DELETE FROM clientes;")
    cursor.execute("DELETE FROM utilizadores;")
    cursor.execute("DELETE FROM formas_pagamento;")
    # Reinicia os contadores de autoincremento
    cursor.execute(
        "UPDATE sqlite_sequence SET seq = 0 WHERE name IN ('reservas', 'veiculos', 'clientes', 'utilizadores', 'formas_pagamento');")
    conn.commit()
    logging.info("Tabelas limpas.")


def popular_dados_base(conn):
    """Popula dados essenciais como formas de pagamento e um usuário admin."""
    cursor = conn.cursor()
    logging.info("Populando dados base...")
    # Formas de Pagamento
    formas_pagamento = ['Cartão de Crédito', 'PIX', 'Dinheiro', 'Transferência Bancária']
    for forma in formas_pagamento:
        cursor.execute("INSERT INTO formas_pagamento (nome) VALUES (?)", (forma,))

    # Usuário Admin
    # ATUALIZADO: Passa a conexão 'conn' para a função
    db.adicionar_utilizador("Admin User", "admin@lw.com", "1234", "Gerente", conn_externa=conn)

    logging.info("Dados base populados.")


def popular_veiculos(conn, quantidade=50):
    """Gera e insere veículos fictícios."""
    cursor = conn.cursor()
    logging.info(f"Populando {quantidade} veículos...")
    marcas_modelos = {
        'BMW': ['Série 3', 'Série 5', 'X3', 'X5', 'i4'],
        'Mercedes-Benz': ['A-Class', 'C-Class', 'E-Class', 'GLC'],
        'Audi': ['A3', 'A4', 'Q3', 'Q5'],
        'Jaguar': ['F-Pace', 'E-Pace'],
        'Land Rover': ['Evoque', 'Velar'],
        'Volvo': ['XC40', 'XC60'],
        'Porsche': ['Macan', 'Cayenne']
    }
    cores = ['Preto', 'Branco', 'Prata', 'Cinza', 'Azul Escuro', 'Vermelho']

    for _ in range(quantidade):
        marca = random.choice(list(marcas_modelos.keys()))
        modelo = random.choice(marcas_modelos[marca])
        ano = random.randint(2020, 2024)
        placa = fake.license_plate()
        cor = random.choice(cores)
        valor_diaria = random.uniform(300, 1500)
        data_revisao = fake.date_between(start_date='-30d', end_date='+365d')

        cursor.execute(
            "INSERT INTO veiculos (marca, modelo, ano, placa, cor, valor_diaria, data_proxima_revisao, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'disponível')",
            (marca, modelo, ano, placa, cor, round(valor_diaria, 2), data_revisao.strftime('%Y-%m-%d'))
        )
    conn.commit()
    logging.info("Veículos populados.")


def popular_clientes(conn, quantidade=50):
    """Gera e insere clientes fictícios com dados portugueses."""
    logging.info(f"Populando {quantidade} clientes (PT-PT)...")
    cursor = conn.cursor()

    for _ in range(quantidade):
        try:
            nome = fake.name()
            email = fake.unique.email()

            # CORREÇÃO: O provedor 'pt_PT' usa o método ssn() para gerar o NIF.
            nif = fake.ssn()

            # Geração do CC (mantém-se igual)
            cc_num = fake.random_number(digits=8, fix_len=True)
            cc_check = "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
            cc = f"{cc_num}{cc_check}"

            cursor.execute(
                "INSERT INTO clientes (nome_completo, nif, telefone, email, cc) VALUES (?, ?, ?, ?, ?)",
                (nome, nif, fake.phone_number(), email, cc)
            )
        except sqlite3.IntegrityError:
            continue
    conn.commit()
    logging.info("Clientes populados.")


def popular_reservas_avancado(conn, quantidade=150):
    """
    Gera e insere reservas de forma inteligente, respeitando a disponibilidade dos veículos.
    """
    logging.info(f"Populando {quantidade} reservas com lógica avançada...")
    cursor = conn.cursor()

    ids_clientes = [row['id'] for row in cursor.execute("SELECT id FROM clientes").fetchall()]
    veiculos = cursor.execute("SELECT id, valor_diaria FROM veiculos").fetchall()
    ids_pagamento = [row['id'] for row in cursor.execute("SELECT id FROM formas_pagamento").fetchall()]

    if not ids_clientes or not veiculos:
        logging.error("Não há clientes ou veículos suficientes para criar reservas.")
        return

    reservas_criadas = 0
    tentativas = 0
    max_tentativas = quantidade * 5

    while reservas_criadas < quantidade and tentativas < max_tentativas:
        tentativas += 1


        veiculo_escolhido = random.choice(veiculos)
        id_veiculo = veiculo_escolhido['id']

        data_inicio = fake.date_time_between(start_date='-1y', end_date='+30d')
        duracao = timedelta(days=random.randint(2, 12))
        data_fim = data_inicio + duracao

        data_inicio_str = data_inicio.strftime('%Y-%m-%d %H:%M:%S')
        data_fim_str = data_fim.strftime('%Y-%m-%d %H:%M:%S')

        if not db.verificar_disponibilidade_veiculo(id_veiculo, data_inicio_str, data_fim_str):
            continue

        cursor.execute("""
            SELECT COUNT(*) FROM reservas
            WHERE id_veiculo = ? AND (
                (data_inicio BETWEEN ? AND ?) OR
                (data_fim BETWEEN ? AND ?) OR
                (? BETWEEN data_inicio AND data_fim)
            )
        """, (id_veiculo, data_inicio, data_fim, data_inicio, data_fim, data_inicio))

        conflitos = cursor.fetchone()[0]

        if conflitos > 0:
            continue

        id_cliente = random.choice(ids_clientes)
        id_forma_pagamento = random.choice(ids_pagamento)
        valor_total = veiculo_escolhido['valor_diaria'] * duracao.days
        status = 'concluída'

        hoje = datetime.now()
        if data_inicio <= hoje < data_fim:
            status = 'ativa'
        elif data_inicio > hoje:
            status = 'ativa'

        if random.random() < 0.05:
            status = 'cancelada'

        cursor.execute(
            "INSERT INTO reservas (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, valor_total, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, round(valor_total, 2), status)
        )
        reservas_criadas += 1

    conn.commit()
    logging.info(f"{reservas_criadas} reservas criadas com sucesso.")


def atualizar_status_veiculos(conn):
    """
    Atualiza o status dos veículos com base nas reservas 'ativas' que estão ocorrendo hoje.
    """
    logging.info("Atualizando status dos veículos...")
    cursor = conn.cursor()
    hoje = datetime.now()

    cursor.execute("UPDATE veiculos SET status = 'disponível'")
    cursor.execute("""
        SELECT id_veiculo FROM reservas 
        WHERE status = 'ativa' AND ? BETWEEN data_inicio AND data_fim
    """, (hoje,))

    ids_veiculos_alugados = [row['id_veiculo'] for row in cursor.fetchall()]

    if ids_veiculos_alugados:
        placeholders = ','.join('?' for _ in ids_veiculos_alugados)
        sql = f"UPDATE veiculos SET status = 'alugado' WHERE id IN ({placeholders})"
        cursor.execute(sql, ids_veiculos_alugados)

    conn.commit()
    logging.info(f"{len(ids_veiculos_alugados)} veículos marcados como 'alugado'.")


def main():
    """Função principal para executar todo o processo de população."""
    conn = db.conectar_bd()
    if not conn: return

    resposta = input("ATENÇÃO: Este script irá apagar TODOS os dados do banco. Deseja continuar? (s/N): ")
    if resposta.lower() != 's':
        logging.info("Operação cancelada.")
        conn.close()
        return

    try:
        limpar_tabelas(conn)
        popular_dados_base(conn)
        popular_veiculos(conn, 50)
        popular_clientes(conn, 50)
        popular_reservas_avancado(conn, 150)
        atualizar_status_veiculos(conn)
        logging.info("\nBanco de dados populado com sucesso e status atualizado!")
    except Exception as e:
        logging.error("Ocorreu um erro durante a população.", exc_info=True)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
