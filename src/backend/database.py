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
            v.id,
            v.marca,
            v.modelo,
            v.ano,
            v.placa,
            v.cor,
            v.valor_diaria,
            v.data_proxima_revisao,
            v.imagem_path,
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
    """
    Remove um veículo do banco de dados. Retorna True em caso de sucesso,
    False se o veículo tiver reservas (IntegrityError) ou outro erro ocorrer.
    """
    sql = "DELETE FROM veiculos WHERE id = ?"
    conn = None

    try:
        conn = conectar_bd()
        if not conn:
            logging.error("Não foi possível obter conexão com o banco de dados para deletar veículo.")
            return False

        cursor = conn.cursor()
        cursor.execute(sql, (id_veiculo,))
        conn.commit()

        # Se cursor.rowcount > 0, significa que a linha foi encontrada e deletada.
        return cursor.rowcount > 0

    except sqlite3.IntegrityError:
        # Se o veículo tiver reservas, a FOREIGN KEY constraint vai falhar.
        if conn:
            conn.rollback()
        logging.warning(f"Tentativa de deletar veículo ID {id_veiculo} com reservas associadas. Operação abortada.")
        return False

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro de banco de dados ao tentar deletar veículo ID {id_veiculo}: {e}", exc_info=True)
        return False

    finally:
        if conn:
            conn.close()

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
        SELECT r.data_inicio, r.data_fim, r.status, c.nome_completo, c.nif
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
    try:
        with conectar_bd() as conn:
            cursor = conn.cursor()
            # O 'try...except' para a falha de integridade fica DENTRO do 'with'
            try:
                cursor.execute(sql, (nome_completo, nif, telefone, email, cc))
                # O commit é automático ao sair do 'with' sem erros
                return True
            except sqlite3.IntegrityError:
                logging.warning(f"Falha ao adicionar cliente. Dados duplicados (NIF, Email ou CC) para: {nif}/{email}")
                return False
    except sqlite3.Error as e:
        # Captura erros de conexão ou outros erros do SQLite
        logging.error(f"Erro de banco de dados ao tentar adicionar cliente: {e}", exc_info=True)
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
    """
    Remove um cliente do banco de dados. Retorna True em caso de sucesso,
    False se o cliente tiver reservas (IntegrityError) ou outro erro ocorrer.
    """
    sql = "DELETE FROM clientes WHERE id = ?"
    conn = None  # Inicia a variável de conexão como None

    try:
        # Etapa 1: Tenta obter uma conexão
        conn = conectar_bd()
        if not conn:
            logging.error("Não foi possível obter conexão com o banco de dados para deletar cliente.")
            return False

        cursor = conn.cursor()

        # Etapa 2: Executa a operação que pode falhar
        cursor.execute(sql, (id_cliente,))
        conn.commit()  # Faz o commit explícito se a execução for bem-sucedida

        return True

    except sqlite3.IntegrityError:
        # Etapa 3: Captura a falha específica de chave estrangeira
        if conn:
            conn.rollback()  # Desfaz a transação que falhou
        logging.warning(f"Tentativa de deletar cliente ID {id_cliente} com reservas associadas. Operação abortada.")
        return False

    except sqlite3.Error as e:
        # Etapa 4: Captura qualquer outro erro do banco de dados
        if conn:
            conn.rollback()
        logging.error(f"Erro de banco de dados ao tentar deletar cliente ID {id_cliente}: {e}", exc_info=True)
        return False

    finally:
        # Etapa 5: Garante que a conexão seja sempre fechada
        if conn:
            conn.close()

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
            d_inicio = datetime.strptime(data_inicio, '%Y-%m-%d %H:%M:%S')
            d_fim = datetime.strptime(data_fim, '%Y-%m-%d %H:%M:%S')

            num_dias = (d_fim - d_inicio).days
            if num_dias < 0:  # Uma reserva pode ser de 0 dias (retirada e entrega no mesmo dia)
                return False

            # Garante pelo menos 1 dia de cobrança
            dias_cobranca = num_dias if num_dias > 0 else 1
            valor_total = veiculo['valor_diaria'] * dias_cobranca

            cursor.execute(sql_insert_reserva,
                           (id_cliente, id_veiculo, id_forma_pagamento, data_inicio, data_fim, valor_total))
            #cursor.execute(sql_update_veiculo, (id_veiculo,))

            return True


    except (ValueError, Exception) as e:

        logging.error(f"Um erro inesperado ocorreu ao criar a reserva: {e}", exc_info=True)

        return False

def listar_reservas():
    sql = "SELECT * FROM reservas ORDER BY data_inicio DESC"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()


def atualizar_reserva(reserva_id, nova_data_inicio, nova_data_fim):
    """
    Atualiza as datas de uma reserva após verificar a disponibilidade do veículo,
    ignorando a própria reserva na verificação de conflitos.
    """
    # 1. Pega o ID do veículo da reserva que estamos editando
    reserva_atual = buscar_reserva_por_id(reserva_id)
    if not reserva_atual:
        return False, "Reserva não encontrada."
    id_veiculo = reserva_atual['id_veiculo']

    # 2. Verifica a disponibilidade, ignorando a própria reserva
    if not verificar_disponibilidade_veiculo(id_veiculo, nova_data_inicio, nova_data_fim, id_reserva_existente=reserva_id):
        return False, "Conflito de datas. O veículo não está disponível no novo período solicitado."

    # 3. Se não houver conflito, atualiza a reserva
    sql = "UPDATE reservas SET data_inicio = ?, data_fim = ? WHERE id = ?"
    try:
        with conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (nova_data_inicio, nova_data_fim, reserva_id))
            return True, "Reserva atualizada com sucesso."
    except sqlite3.Error as e:
        logging.error(f"Erro ao atualizar reserva ID {reserva_id}: {e}", exc_info=True)
        return False, "Ocorreu um erro no banco de dados."

def deletar_reserva(reserva_id):
    """Deleta uma reserva do banco de dados."""
    sql = "DELETE FROM reservas WHERE id = ?"
    try:
        with conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (reserva_id,))
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logging.error(f"Erro ao deletar reserva ID {reserva_id}: {e}", exc_info=True)
        return False

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
        WHERE id_veiculo = ? AND status != 'cancelada' AND (
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

def listar_todas_reservas_detalhadas():
    """
    Lista todas as reservas com detalhes do cliente e do veículo.
    """
    sql = """
        SELECT
            r.id AS reserva_id,
            r.data_inicio,
            r.data_fim,
            r.status,
            c.nome_completo AS cliente_nome,
            v.marca,
            v.modelo,
            v.placa
        FROM reservas r
        JOIN clientes c ON r.id_cliente = c.id
        JOIN veiculos v ON r.id_veiculo = v.id
        ORDER BY r.data_inicio DESC
    """
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

def buscar_reserva_por_id(reserva_id):
    """Busca uma única reserva pelos seus detalhes."""
    sql = "SELECT * FROM reservas WHERE id = ?"
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (reserva_id,))
        return cursor.fetchone()