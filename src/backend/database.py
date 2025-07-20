import logging
import sqlite3
import bcrypt
import os
from datetime import date, timedelta, datetime


# --- Configuração do Banco de Dados ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'data', 'luxury_wheels.db')

def conectar_bd():
    """Cria e retorna uma conexão com o banco de dados."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}", exc_info=True)
        return None


# --- Funções de Segurança ---
def hash_senha(senha):
    """Gera um hash seguro para a senha."""
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verificar_senha(senha, hash_armazenado):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))


# --- CRUD: Utilizadores ---
def adicionar_utilizador(nome, email, senha, cargo, conn_externa=None):
    """
    Adiciona um novo utilizador. Se uma conexão externa for fornecida,
    usa-a. Caso contrário, cria uma nova.
    """
    senha_hashed = hash_senha(senha)
    sql = "INSERT INTO utilizadores (nome, email, senha, cargo) VALUES (?, ?, ?, ?)"

    def _operacao(cursor):
        cursor.execute(sql, (nome, email, senha_hashed, cargo))

    try:
        if conn_externa:
            # Opera na conexão/transação existente
            _operacao(conn_externa.cursor())
            # O commit será feito pelo chamador
        else:
            # Gerencia a própria conexão
            with conectar_bd() as conn:
                _operacao(conn.cursor())
                # O commit é automático aqui
        return True
    except sqlite3.IntegrityError:
        logging.warning(f"Tentativa de adicionar usuário com email duplicado: {email}")
        return False
    except Exception as e:
        # O erro de 'database is locked' acontecerá aqui se chamado incorretamente
        logging.error(f"Erro inesperado ao adicionar usuário: {e}", exc_info=True)
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
    """
    Retorna uma lista de todos os veículos, incluindo um campo dinâmico
    'status_dinamico' se o veículo estiver alugado hoje.
    """
    hoje = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql = """
        SELECT 
            v.*,
            CASE 
                WHEN r.id IS NOT NULL THEN 'Alugado'
                ELSE v.status -- Mantém o status original (ex: 'manutenção')
            END AS status_dinamico,
            r.data_fim AS data_retorno
        FROM veiculos v
        LEFT JOIN reservas r ON v.id = r.id_veiculo 
                             AND r.status = 'ativa' 
                             AND ? BETWEEN r.data_inicio AND r.data_fim
        ORDER BY v.marca, v.modelo
    """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (hoje,))
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
    """Deleta um veículo, se ele não tiver reservas associadas."""
    sql = "DELETE FROM veiculos WHERE id = ?"
    with conectar_bd() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (id_veiculo,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Ocorre se uma chave estrangeira (reserva) aponta para este veículo
            return False

def buscar_veiculos_com_devolucao_hoje():
    hoje_str = date.today().strftime('%Y/%m/%d')
    sql = """
            SELECT v.id FROM veiculos v
            JOIN reservas r ON v.id = r.id_veiculo
            WHERE r.status = 'ativa' AND DATE(r.data_fim) = ?
        """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (hoje_str,))
        # Retorna um conjunto de IDs para busca rápida
        return {row['id'] for row in cursor.fetchall()}

def buscar_reservas_por_veiculo(id_veiculo):
    sql = """
        SELECT r.data_inicio, r.data_fim, c.nome_completo, c.nif
        FROM reservas r
        JOIN clientes c ON r.id_cliente = c.id
        WHERE r.id_veiculo = ? ORDER BY r.data_inicio DESC
    """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_veiculo,))
        return cursor.fetchall()

def buscar_veiculo_por_id(id_veiculo):
    """Busca um único veículo pelo seu ID."""
    sql = "SELECT * FROM veiculos WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_veiculo,))
        return cursor.fetchone()

# --- CRUD: Clientes ---
def adicionar_cliente(nome_completo, nif, telefone, email, cc, cursor=None):
    sql = "INSERT INTO clientes (nome_completo, nif, telefone, email, cc) VALUES (?, ?, ?, ?, ?)"
    if conn is None:
        try:
            with conectar_bd() as conn_local:
                conn_local.execute(sql, (nome_completo, nif, telefone, email, cc))
                return True
        except sqlite3.IntegrityError:
            return False
    else:
        try:
            conn.execute(sql, (nome_completo, nif, telefone, email, cc))
            return True
        except sqlite3.IntegrityError:
            return False

def listar_clientes():
    sql = "SELECT * FROM clientes ORDER BY nome_completo"
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
    """
    Adiciona uma nova reserva e atualiza o status do veículo.
    Operação transacional e robusta usando gerenciador de contexto.
    """
    sql_get_veiculo = "SELECT valor_diaria, status FROM veiculos WHERE id = ?"
    sql_insert_reserva = """
        INSERT INTO reservas (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, valor_total, status)
        VALUES (?, ?, ?, ?, ?, ?, 'ativa')
    """
    sql_update_veiculo = "UPDATE veiculos SET status = 'alugado' WHERE id = ?"


    try:
        with conectar_bd() as conn:
            cursor = conn.cursor()


            cursor.execute(sql_get_veiculo, (id_veiculo,))
            veiculo = cursor.fetchone()
            if not veiculo or veiculo['status'] != 'disponível':
                logging.error(f"Erro: Veículo {id_veiculo} não está disponível para reserva.", exc_info=True)
                return False


            valor_diaria = veiculo['valor_diaria']
            # Assume que o formato da data já está correto (YYYY-MM-DD)
            d_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            d_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            num_dias = (d_fim - d_inicio).days
            if num_dias <= 0:
                logging.error("Erro: A data de fim deve ser posterior à data de início.", exc_info=True)
                return False

            valor_total = valor_diaria * num_dias


            cursor.execute(sql_insert_reserva,
                           (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, valor_total))

            cursor.execute(sql_update_veiculo, (id_veiculo,))

            return True

    except sqlite3.IntegrityError as e:
        # Ocorre se id_cliente ou outra FK for inválida. O rollback é automático com 'with' em caso de exceção.
        logging.error(f"Erro de integridade ao criar reserva: {e}", exc_info=True)
        return False
    except (ValueError, Exception) as e:
        # Captura outros erros (ex: formato de data inválido)
        logging.error(f"Um erro inesperado ocorreu ao criar a reserva: {e}", exc_info=True)
        return False


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

# Em src/backend/database.py
def buscar_reservas_por_cliente(id_cliente):
    """Busca todas as reservas de um cliente, juntando com dados do veículo."""
    sql = """
        SELECT
            r.id,
            r.data_inicio,
            r.data_fim,
            r.status AS status_reserva,
            v.marca,
            v.modelo,
            v.placa
        FROM reservas r
        JOIN veiculos v ON r.id_veiculo = v.id
        WHERE r.id_cliente = ?
        ORDER BY r.data_inicio DESC
    """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_cliente,))
        return cursor.fetchall()

# --- CRUD: Formas de Pagamento ---
def listar_formas_pagamento():
    sql = "SELECT * FROM formas_pagamento ORDER BY nome"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()


# Em src/backend/database.py
def importar_clientes_de_csv(caminho_arquivo):
    """
    Importa clientes de um arquivo CSV para o banco de dados.
    Retorna a contagem de sucessos e falhas.
    """
    import pandas as pd
    import logging

    sucessos = 0
    falhas = 0
    erros_detalhados = []

    try:
        df = pd.read_csv(caminho_arquivo, sep=';', dtype=str).fillna('')

        colunas_obrigatorias = {'nome_completo', 'nif', 'telefone', 'email', 'cc'}
        if not colunas_obrigatorias.issubset(df.columns):
            msg = f"Arquivo CSV deve conter as colunas: {', '.join(colunas_obrigatorias)}"
            logging.error(msg)
            return 0, 0, [msg]

        # CORREÇÃO: Usamos o with aqui para garantir que a transação seja gerenciada
        with conectar_bd() as conn:
            cursor = conn.cursor()
            for index, row in df.iterrows():
                try:
                    # Usando a função já existente para adicionar cliente
                    # A função adicionar_cliente já faz o seu próprio commit, o que não é ideal para um lote.
                    # Vamos inserir diretamente para controlar a transação.
                    cursor.execute(
                        "INSERT INTO clientes (nome_completo, nif, telefone, email, cc) VALUES (?, ?, ?, ?, ?)",
                        (row['nome_completo'], row['nif'], row['telefone'], row['email'], row['cc'])
                    )
                    sucessos += 1
                except (sqlite3.IntegrityError) as e:
                    falhas += 1
                    erros_detalhados.append(
                        f"Linha {index + 2}: NIF/Email/CC '{row.get('nif', 'N/A')}' provavelmente já existe.")
                except KeyError as e:
                    falhas += 1
                    erros_detalhados.append(f"Linha {index + 2}: Coluna faltando - Erro: {e}")

            # Commit é feito uma única vez no final, o que é muito mais performático
            conn.commit()

    except FileNotFoundError:
        msg = "Arquivo de importação não encontrado."
        logging.error(msg)
        erros_detalhados.append(msg)
        return 0, 1, erros_detalhados
    except Exception as e:
        msg = f"Erro inesperado ao processar o arquivo: {e}"
        logging.error(msg, exc_info=True)
        erros_detalhados.append(msg)
        # O total de falhas é o que não foi sucesso.
        total_rows = len(df) if 'df' in locals() else 0
        falhas = total_rows - sucessos
        return sucessos, falhas, erros_detalhados

    return sucessos, falhas, erros_detalhados
def buscar_revisoes_proximas(dias_limite=15):
    """Busca veículos com revisão agendada entre hjoje e a data limite"""
    hoje = date.today()
    data_limite = hoje + timedelta(days=dias_limite)
    sql = """
            SELECT id, marca, modelo, placa, data_proxima_revisao 
            FROM veiculos 
            WHERE data_proxima_revisao BETWEEN ? AND ?
            ORDER BY data_proxima_revisao ASC
        """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (hoje.strftime('%Y-%m-%d'), data_limite.strftime('%Y-%m-%d')))
        return cursor.fetchall()


def buscar_revisoes_vencidas():
    """Busca veículos cuja data de revisão já passou e não foi atualizada."""
    hoje = date.today()
    sql = """
            SELECT id, marca, modelo, placa, data_proxima_revisao 
            FROM veiculos 
            WHERE data_proxima_revisao < ?
            ORDER BY data_proxima_revisao DESC
        """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (hoje.strftime('%Y-%m-%d'),))
        return cursor.fetchall()

def importar_clientes_de_csv(caminho_arquivo):
    import pandas as pd

    sucessos = 0
    falhas = 0
    erros_detalhados = []

    try:
        df = pd.read_csv(caminho_arquivo, sep=';', dtype=str)

        colunas_obrigatorias = {'nome_completo', 'nif', 'telefone', 'email', 'cc'}
        if not colunas_obrigatorias.issubset(df.columns):
            return 0, 0, [f"Arquivo CSV deve conter as colunas: {', '.join(colunas_obrigatorias)}"]

        with conectar_bd() as conn:
            cursor = conn.cursor()
            for index, row in df.iterrows():
                try:
                    if adicionar_cliente(
                        row['nome_completo'], row['nif'],
                        row['telefone'], row['email'], row['cc'],
                        cursor_existente=cursor
                    ):
                        sucessos += 1
                    else:
                        falhas += 1
                        erros_detalhados.append(
                            f"Linha {index + 2}: NIF/Email/CC '{row.get('nif', 'N/A')}' provavelmente já existe.")

                except KeyError as e:
                    falhas += 1
                    erros_detalhados.append(f"Linha{index + 2}: Coluna faltando - Erro: {e}")

            conn.commit()

    except Exception as e:
        erros_detalhados.append(f"Erro inesperado ao processar o arquivo: {e}")
        return sucessos, falhas, erros_detalhados
    return sucessos, falhas, erros_detalhados

def listar_veiculos_disponiveis():
    """Retorna uma lista de todos os veículos com status 'disponível'."""
    sql = "SELECT * FROM veiculos WHERE status = 'disponível' ORDER BY marca, modelo"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

def buscar_veiculo_por_id(id_veiculo):
    """Busca um único veículo pelo seu ID."""
    sql = "SELECT * FROM veiculos WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_veiculo,))
        return cursor.fetchone()

def verificar_disponibilidade_veiculo(id_veiculo, data_inicio, data_fim, id_reserva_existente=None):
    """
    Verifica se um veículo está disponível em um dado período,
    opcionalmente ignorando uma reserva existente (para o caso de edição).
    Retorna True se disponível, False se houver conflito.
    """
    sql = """
        SELECT COUNT(*) FROM reservas
        WHERE id_veiculo = ? AND (
            (data_inicio <= ? AND data_fim >= ?) OR -- Reserva existente engloba o novo período
            (data_inicio >= ? AND data_inicio <= ?) OR -- Início da nova reserva conflita
            (data_fim >= ? AND data_fim <= ?) -- Fim da nova reserva conflita
        )
    """
    params = [id_veiculo, data_inicio, data_fim, data_inicio, data_fim, data_inicio, data_fim]

    if id_reserva_existente:
        sql += " AND id != ?"
        params.append(id_reserva_existente)

    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conflitos = cursor.fetchone()[0]
        return conflitos == 0