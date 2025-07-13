# scripts/populate_database.py

import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta
import os
import sys

# Adiciona a pasta 'src' ao path para que possamos importar 'database' e 'config_manager'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from backend import database as db

# Inicializa o Faker para o Brasil
fake = Faker('pt_PT')


def limpar_tabelas(conn):
    """Limpa todos os dados das tabelas para começar do zero."""
    cursor = conn.cursor()
    print("Limpando tabelas existentes...")
    cursor.execute("DELETE FROM reservas;")
    cursor.execute("DELETE FROM veiculos;")
    cursor.execute("DELETE FROM clientes;")
    cursor.execute("DELETE FROM utilizadores;")
    cursor.execute("DELETE FROM formas_pagamento;")
    # Reinicia os contadores de autoincremento
    cursor.execute(
        "UPDATE sqlite_sequence SET seq = 0 WHERE name IN ('reservas', 'veiculos', 'clientes', 'utilizadores', 'formas_pagamento');")
    conn.commit()
    print("Tabelas limpas.")


def popular_dados_base(conn):
    """Popula dados essenciais como formas de pagamento e um usuário admin."""
    cursor = conn.cursor()
    print("Populando dados base...")
    # Formas de Pagamento
    formas_pagamento = ['Cartão de Crédito', 'PIX', 'Dinheiro', 'Transferência Bancária']
    for forma in formas_pagamento:
        cursor.execute("INSERT INTO formas_pagamento (nome) VALUES (?)", (forma,))

    # Usuário Admin
    db.adicionar_utilizador("Admin User", "admin@lw.com", "1234", "Gerente")
    print("Dados base populados.")
    conn.commit()


def popular_veiculos(conn, quantidade=50):
    """Gera e insere veículos fictícios."""
    cursor = conn.cursor()
    print(f"Populando {quantidade} veículos...")
    marcas_modelos = {
        'Mercedes-Benz': ['A-Class', 'C-Class', 'E-Class', 'GLC'],
        'BMW': ['Série 3', 'Série 5', 'X1', 'X3', 'X5'],
        'Audi': ['A3', 'A4', 'Q3', 'Q5'],
        'Jaguar': ['F-Pace', 'E-Pace'],
        'Land Rover': ['Evoque', 'Velar'],
        'Volvo': ['XC40', 'XC60'],
        'Porsche': ['Macan', 'Cayenne']
    }
    cores = ['Preto', 'Branco', 'Prata', 'Cinza', 'Azul', 'Vermelho']

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
    print("Veículos populados.")


def popular_clientes(conn, quantidade=100):
    """Gera e insere clientes fictícios com dados portugueses."""
    cursor = conn.cursor()
    print(f"Populando {quantidade} clientes (PT-PT)...")
    for _ in range(quantidade):
        try:
            nome = fake.name()
            email = fake.unique.email()
            nif = fake.nif()
            cc = f"{fake.random_number(digits=8, fix_len=True)}{random.choice('0123456789JABCDEFGHIKLMNPQRSTUVWXYZ')}{random.choice('0123456789JABCDEFGHIKLMNPQRSTUVWXYZ')}{random.choice('0123456789JABCDEFGHIKLMNPQRSTUVWXYZ')}{random.choice('0123456789JABCDEFGHIKLMNPQRSTUVWXYZ')}"

            cursor.execute(
                "INSERT INTO clientes (nome_completo, nif, telefone, email, cc) VALUES (?, ?, ?, ?, ?)",
                (nome, nif, fake.phone_number(), email, cc)
            )
        except sqlite3.IntegrityError:
            # Ignora duplicatas que podem raramente acontecer e continua
            continue
    conn.commit()
    print("Clientes populados.")


def popular_reservas(conn, quantidade=200):
    """Gera e insere reservas fictícias, vinculando clientes e veículos existentes."""
    cursor = conn.cursor()
    print(f"Populando {quantidade} reservas...")

    # Pega IDs existentes para criar links válidos
    ids_clientes = [row[0] for row in cursor.execute("SELECT id FROM clientes").fetchall()]
    ids_veiculos = [row[0] for row in cursor.execute("SELECT id FROM veiculos").fetchall()]
    ids_pagamento = [row[0] for row in cursor.execute("SELECT id FROM formas_pagamento").fetchall()]

    for _ in range(quantidade):
        id_cliente = random.choice(ids_clientes)
        id_veiculo = random.choice(ids_veiculos)
        id_forma_pagamento = random.choice(ids_pagamento)

        data_inicio = fake.date_time_between(start_date='-1y', end_date='+30d')
        duracao = timedelta(days=random.randint(2, 15))
        data_fim = data_inicio + duracao

        # Busca valor da diária para calcular o total
        valor_diaria = cursor.execute("SELECT valor_diaria FROM veiculos WHERE id = ?", (id_veiculo,)).fetchone()[0]
        valor_total = valor_diaria * duracao.days

        status = random.choices(['ativa', 'concluída', 'cancelada'], weights=[10, 85, 5], k=1)[0]

        cursor.execute(
            "INSERT INTO reservas (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, valor_total, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, valor_total, status)
        )
    conn.commit()
    print("Reservas populadas.")


def main():
    """Função principal para executar todo o processo de população."""
    # Usa a função de conexão do nosso módulo de database
    conn = db.conectar_bd()
    if not conn:
        print("Não foi possível conectar ao banco de dados.")
        return

    # Confirmação do usuário para evitar destruição acidental de dados
    resposta = input(
        "ATENÇÃO: Este script irá apagar TODOS os dados do banco de dados atual. Deseja continuar? (s/N): ")
    if resposta.lower() != 's':
        print("Operação cancelada.")
        conn.close()
        return

    try:
        limpar_tabelas(conn)
        popular_dados_base(conn)
        popular_veiculos(conn, 50)
        popular_clientes(conn, 100)
        popular_reservas(conn, 200)
        print("\nBanco de dados populado com sucesso!")
    except Exception as e:
        print(f"\nOcorreu um erro: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()