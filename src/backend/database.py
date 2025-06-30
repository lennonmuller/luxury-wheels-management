import sqlite3
import bcrypt
import os
from datetime import date, timedelta


# --- Configuração do Banco de Dados ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'data', 'luxury_wheels.db')

def conectar_bd():
    """Cria e retorna uma conexão com o banco de dados."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


# --- Funções de Segurança ---
def hash_senha(senha):
    """Gera um hash seguro para a senha."""
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verificar_senha(senha, hash_armazenado):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))


# --- CRUD: Utilizadores ---
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
        except sqlite3.IntegrityError:
            return False


def buscar_utilizador_por_email(email):
    """Busca um utilizador pelo seu email."""
    sql = "SELECT * FROM utilizadores WHERE email = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (email,))
        return cursor.fetchone()


# --- CRUD: Veículos ---
def adicionar_veiculo(marca, modelo, ano, placa, cor, valor_diaria, data_proxima_revisao, imagem_path=None):
    sql = "INSERT INTO veiculos (marca, modelo, ano, placa, cor, valor_diaria, data_proxima_revisao, imagem_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (marca, modelo, ano, placa, cor, valor_diaria, data_proxima_revisao, imagem_path))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def listar_veiculos():
    sql = "SELECT * FROM veiculos ORDER BY marca, modelo"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()


def atualizar_veiculo(id_veiculo, **kwargs):
    campos = ", ".join([f"{chave} = ?" for chave in kwargs.keys()])
    valores = list(kwargs.values()) + [id_veiculo]
    sql = f"UPDATE veiculos SET {campos} WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, valores)
        conn.commit()


def deletar_veiculo(id_veiculo):
    sql = "DELETE FROM veiculos WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_veiculo,))
        conn.commit()

def listar_veiculos_para_revisao(dias_ate_revisao=15):
    """Lista veículos cuja próxima revisão está dentro do intervalo de dias especificado."""
    data_limite = date.today() + timedelta(days=dias_ate_revisao)
    sql = "SELECT id, marca, modelo, placa, data_proxima_revisao FROM veiculos WHERE data_proxima_revisao <= ? ORDER BY data_proxima_revisao ASC"

    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (data_limite.strftime('%d/%m/%Y'),))
        return cursor.fetchall()

# --- CRUD: Clientes ---
def adicionar_cliente(nome_completo, cpf, telefone, email, cnh):
    sql = "INSERT INTO clientes (nome_completo, cpf, telefone, email, cnh) VALUES (?, ?, ?, ?, ?)"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (nome_completo, cpf, telefone, email, cnh))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def listar_clientes():
    sql = "SELECT * FROM clientes ORDER BY nome_completo"  # Corrigido: nome_completo
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()


def atualizar_cliente(id_cliente, **kwargs):
    campos = ", ".join([f"{chave} = ?" for chave in kwargs.keys()])
    valores = list(kwargs.values()) + [id_cliente]
    sql = f"UPDATE clientes SET {campos} WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, valores)
        conn.commit()


def deletar_cliente(id_cliente):
    sql = "DELETE FROM clientes WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_cliente,))
        conn.commit()


# --- CRUD: Reservas ---
def adicionar_reserva(id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim):
    conn = conectar_bd()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT valor_diaria, status FROM veiculos WHERE id = ?", (id_veiculo,))
        veiculo = cursor.fetchone()
        if not veiculo or veiculo['status'] != 'disponível':
            return False

        d_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        d_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        num_dias = (d_fim - d_inicio).days
        if num_dias <= 0: return False

        valor_total = veiculo['valor_diaria'] * num_dias

        sql_insert_reserva = "INSERT INTO reservas (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, valor_total, status) VALUES (?, ?, ?, ?, ?, ?, 'ativa')"
        cursor.execute(sql_insert_reserva,
                       (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, valor_total))

        sql_update_veiculo = "UPDATE veiculos SET status = 'alugado' WHERE id = ?"
        cursor.execute(sql_update_veiculo, (id_veiculo,))

        conn.commit()
        return True
    except (sqlite3.IntegrityError, ValueError, Exception) as e:
        print(f"Erro ao adicionar reserva: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()


def listar_reservas():
    sql = "SELECT * FROM reservas ORDER BY data_inicio DESC"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()


def atualizar_reserva(id_reserva, **kwargs):
    campos = ", ".join([f"{chave} = ?" for chave in kwargs.keys()])
    valores = list(kwargs.values()) + [id_reserva]
    sql = f"UPDATE reservas SET {campos} WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, valores)
        conn.commit()


def deletar_reserva(id_reserva):
    sql = "DELETE FROM reservas WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_reserva,))
        conn.commit()


# --- CRUD: Formas de Pagamento ---
def listar_formas_pagamento():
    sql = "SELECT * FROM formas_pagamento ORDER BY nome"  # Corrigido
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
