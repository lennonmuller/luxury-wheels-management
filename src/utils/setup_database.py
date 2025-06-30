# src/utils/setup_database.py

import os
import sqlite3
import sys

# Adiciona o diretório raiz para poder importar do backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.backend import database as db

# Este é o código SQL que definimos na Fase 1.
# Mantê-lo aqui centraliza a definição da estrutura do banco.
SQL_SCHEMA_SCRIPT = """
    -- Tabela de Utilizadores do sistema (funcionários, gerentes)
    CREATE TABLE IF NOT EXISTS utilizadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        cargo TEXT NOT NULL
    );

    -- Tabela de Clientes da locadora
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_completo TEXT NOT NULL,
        cpf TEXT NOT NULL UNIQUE,
        telefone TEXT,
        email TEXT UNIQUE,
        cnh TEXT NOT NULL UNIQUE
    );

    -- Tabela de Veículos da frota
    CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marca TEXT NOT NULL,
        modelo TEXT NOT NULL,
        ano INTEGER NOT NULL,
        placa TEXT NOT NULL UNIQUE,
        cor TEXT,
        valor_diaria REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'disponível',
        data_proxima_revisao DATE NOT NULL,
        imagem_path TEXT
    );

    -- Tabela de Formas de Pagamento aceitas
    CREATE TABLE IF NOT EXISTS formas_pagamento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    );

    -- Tabela de Reservas (a tabela que conecta tudo)
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL,
        id_veiculo INTEGER NOT NULL,
        id_forma_pagamento INTEGER,
        data_inicio DATETIME NOT NULL,
        data_fim DATETIME NOT NULL,
        valor_total REAL,
        status TEXT NOT NULL DEFAULT 'ativa',
        FOREIGN KEY (id_cliente) REFERENCES clientes(id),
        FOREIGN KEY (id_veiculo) REFERENCES veiculos(id),
        FOREIGN KEY (id_forma_pagamento) REFERENCES formas_pagamento(id)
    );
"""


def criar_tabelas():
    """Conecta ao banco de dados e executa o script de criação de tabelas."""
    print("Verificando e criando tabelas, se necessário...")
    try:
        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            # O método executescript permite rodar múltiplos comandos SQL de uma vez
            cursor.executescript(SQL_SCHEMA_SCRIPT)
            conn.commit()
        print("Tabelas verificadas/criadas com sucesso.")
    except sqlite3.Error as e:
        print(f"Ocorreu um erro ao criar as tabelas: {e}")


if __name__ == "__main__":
    # Remove o banco de dados antigo para um novo começo.
    # Use com CUIDADO!
    if os.path.exists(db.DB_PATH):
        print(f"Removendo banco de dados antigo em: {db.DB_PATH}")
        os.remove(db.DB_PATH)

    criar_tabelas()
