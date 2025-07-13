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
def adicionar_cliente(nome_completo, telefone, email, nif, cc):
    sql = "INSERT INTO clientes (nome_completo, telefone, email, nif, cc) VALUES (?, ?, ?, ?, ?)"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (nome_completo, telefone, email, nif, cc))
            conn.commit()
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
                print(f"Erro: Veículo {id_veiculo} não está disponível para reserva.")
                return False


            valor_diaria = veiculo['valor_diaria']
            # Assume que o formato da data já está correto (YYYY-MM-DD)
            d_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            d_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            num_dias = (d_fim - d_inicio).days
            if num_dias <= 0:
                print("Erro: A data de fim deve ser posterior à data de início.")
                return False

            valor_total = valor_diaria * num_dias


            cursor.execute(sql_insert_reserva,
                           (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, valor_total))

            cursor.execute(sql_update_veiculo, (id_veiculo,))

            return True

    except sqlite3.IntegrityError as e:
        # Ocorre se id_cliente ou outra FK for inválida. O rollback é automático com 'with' em caso de exceção.
        print(f"Erro de integridade ao criar reserva: {e}")
        return False
    except (ValueError, Exception) as e:
        # Captura outros erros (ex: formato de data inválido)
        print(f"Um erro inesperado ocorreu ao criar a reserva: {e}")
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

def importar_veiculos_de_csv(caminho_arquivo):
    """
        Importa veículos de um arquivo CSV para o banco de dados.
        Retorna a contagem de sucessos e falhas.
        """
    import pandas as pd  # Importação local para manter o resto do módulo leve

    sucessos = 0
    falhas = 0
    erros_detalhados = []

    try:
        df = pd.read_csv(caminho_arquivo, sep=';', dtype=str)

        # Validação básica das colunas esperadas
        colunas_obrigatorias = {'marca', 'modelo', 'ano', 'placa', 'cor', 'valor_diaria', 'data_proxima_revisao'}
        if not colunas_obrigatorias.issubset(df.columns):
            return 0, 0, [f"Arquivo CSV deve conter as colunas: {', '.join(colunas_obrigatorias)}"]

        with conectar_bd() as conn:
            cursor = conn.cursor()
            for index, row in df.iterrows():
                try:
                    # Tenta inserir cada linha na tabela de veículos
                    sql = "INSERT INTO veiculos (marca, modelo, ano, placa, cor, valor_diaria, data_proxima_revisao, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'disponível')"
                    cursor.execute(sql, (
                        row['marca'], row['modelo'], int(row['ano']), row['placa'],
                        row['cor'], float(row['valor_diaria']), row['data_proxima_revisao']
                    ))
                    sucessos += 1
                except (sqlite3.IntegrityError, ValueError, KeyError) as e:
                    # Captura erros de placa duplicada, conversão de tipo ou coluna faltando
                    falhas += 1
                    erros_detalhados.append(f"Linha {index + 2}: Placa '{row.get('placa', 'N/A')}' - Erro: {e}")

            conn.commit()

    except FileNotFoundError:
        erros_detalhados.append("Arquivo não encontrado.")
        return 0, 1, erros_detalhados
    except Exception as e:
        erros_detalhados.append(f"Erro inesperado ao processar o arquivo: {e}")
        return sucessos, falhas + (len(df) - sucessos - falhas), erros_detalhados

    return sucessos, falhas, erros_detalhados