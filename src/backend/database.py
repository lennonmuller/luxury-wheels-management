import sqlite3
import bcrypt
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'data', 'luxury_wheels.db')

def conectar_bd():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row #acessar colunas por nome
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao nectar ao banco de dados: {e}")
        return None

def hash_senha(senha):
    senha_bytes = senha.encode('utf-8')
    sal = bcrypt.gensalt()
    hash_gerado = bcrypt.hashpw(senha_bytes, sal)
    return hash_gerado.decode('utf-8')

def verificar_senha(senha, hash_armazenado):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    senha_bytes = senha.encode('utf-8')
    hash_bytes = hash_armazenado.encode('utf-8')
    return bcrypt.checkpw(senha_bytes, hash_bytes)

# funções CRUD para utilizadores

def adicionar_utilizador(nome, email, senha, cargo):
    """Adiciona um novo utilizador, com senha hasheada."""
    senha_hashed = hash_senha(senha)
    sql = "INSERT INTO utilizadores (nome, email, senha, cargo) VALUES (?, ?, ?, ?)"

    with conectar_bd() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (nome, email, senha_hashed, cargo))
            conn.commit()
            return True
        except sqlite3.IntegrityError: # Ocorre se email já existir (UNIQUE)
            return False

def buscar_utilizador_por_email(email):
    """Busca utilizador pelo email."""
    sql = "SELECT * FROM utilizadores WHERE email = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (email,))
        return cursor.fetchone()

# funções CRUD
# Veículos
def adicionar_veiculo(marca, modelo, ano, placa, cor, valor_diaria, data_proxima_revisao, imagem_path=None):
    """Adiciona um novo veículo ao banco de dados."""
    sql = """
        INSERT INTO veiculos (marca, modelo, ano, placa, cor, valor_diaria, data_proxima_revisao, imagem_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (marca, modelo, ano, placa, cor, valor_diaria, data_proxima_revisao, imagem_path))
            conn.commit()
            return True
        except sqlite3.IntegrityError:  # Placa já existe
            return False


def listar_veiculos():
    """Retorna uma lista de todos os veículos."""
    sql = "SELECT * FROM veiculos ORDER BY marca, modelo"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()


def atualizar_veiculo(id_veiculo, **kwargs):
    """Atualiza um veículo. Ex: atualizar_veiculo(1, status='manutenção', valor_diaria=550.0)"""
    campos_para_atualizar = ", ".join([f"{chave} = ?" for chave in kwargs.keys()])
    valores = list(kwargs.values())
    valores.append(id_veiculo)

    sql = f"UPDATE veiculos SET {campos_para_atualizar} WHERE id = ?"

    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, valores)
        conn.commit()


def deletar_veiculo(id_veiculo):
    """Deleta um veículo do banco de dados."""
    sql = "DELETE FROM veiculos WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_veiculo,))
        conn.commit()

# Clientes
def adicionar_cliente(nome, email, telefone, cnh, endereco):
    """Adiciona um novo cliente ao banco de dados."""
    sql = """
        INSERT INTO clientes (nome, email, telefone, cnh, endereco)
        VALUES (?, ?, ?, ?, ?)
    """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (nome, email, telefone, cnh, endereco))
            conn.commit()
            return True
        except sqlite3.IntegrityError:  # Email ou CNH duplicados, se for UNIQUE
            return False


def listar_clientes():
    """Retorna uma lista de todos os clientes."""
    sql = "SELECT * FROM clientes ORDER BY nome"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()


def atualizar_cliente(id_cliente, **kwargs):
    """Atualiza os dados de um cliente."""
    campos_para_atualizar = ", ".join([f"{chave} = ?" for chave in kwargs.keys()])
    valores = list(kwargs.values())
    valores.append(id_cliente)

    sql = f"UPDATE clientes SET {campos_para_atualizar} WHERE id = ?"

    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, valores)
        conn.commit()


def deletar_cliente(id_cliente):
    """Remove um cliente do banco de dados."""
    sql = "DELETE FROM clientes WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_cliente,))
        conn.commit()

# Reservas
def adicionar_reserva(id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim):
    """Adiciona uma nova reserva ao banco de dados."""
    sql = """
        INSERT INTO reservas (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim)
        VALUES (?, ?, ?, ?, ?)
    """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim))
        conn.commit()


def listar_reservas():
    """Lista todas as reservas."""
    sql = "SELECT * FROM reservas ORDER BY data_inicio DESC"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()


def atualizar_reserva(id_reserva, **kwargs):
    """Atualiza os dados de uma reserva."""
    campos_para_atualizar = ", ".join([f"{chave} = ?" for chave in kwargs.keys()])
    valores = list(kwargs.values())
    valores.append(id_reserva)

    sql = f"UPDATE reservas SET {campos_para_atualizar} WHERE id = ?"

    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, valores)
        conn.commit()


def deletar_reserva(id_reserva):
    """Deleta uma reserva do banco de dados."""
    sql = "DELETE FROM reservas WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_reserva,))
        conn.commit()

def listar_reservas_ativas():
    """Lista apenas as reservas ativas (data_fim >= hoje)."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    sql = """
        SELECT * FROM reservas
        WHERE data_fim >= ?
        ORDER BY data_inicio
    """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (hoje,))
        return cursor.fetchall()

# Formas de pagamento
def listar_formas_pagamento():
    """Retorna todas as formas de pagamento disponíveis."""
    sql = "SELECT * FROM formas_pagamento ORDER BY descricao"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
