import unittest
import sys
import os
import sqlite3

# Adiciona a pasta 'src' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from backend import database as db


class TestDatabaseLogic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Configuração executada uma vez antes de todos os testes da classe.
        Ideal para criar uma conexão de banco de dados compartilhada.
        """
        cls.conn = db.conectar_bd()
        cls.assertIsNotNone(cls.conn, "Falha ao conectar ao banco de dados de teste.")
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        """
        Executado uma vez após todos os testes da classe.
        Fecha a conexão com o banco.
        """
        if cls.conn:
            cls.conn.close()

    def setUp(self):
        """Executado antes de cada teste. Garante um estado limpo."""
        # Limpa o usuário de teste para garantir que cada teste seja independente
        self.cursor.execute("DELETE FROM utilizadores WHERE email LIKE '%@unittest.com'")
        self.conn.commit()

    def test_password_hashing_and_verification(self):
        """
        Testa se o hashing da senha funciona e se a verificação é bem-sucedida
        com a senha correta e falha com a senha incorreta.
        """
        senha_original = "senhaSuperSecreta123"
        hash_gerado = db.hash_senha(senha_original)

        self.assertNotEqual(senha_original, hash_gerado)
        self.assertIsInstance(hash_gerado, str)
        self.assertTrue(db.verificar_senha(senha_original, hash_gerado))
        self.assertFalse(db.verificar_senha("senhaErrada", hash_gerado))

    def test_add_and_find_user(self):
        """
        Testa a adição e busca de um usuário usando uma única transação de teste.
        """
        # Dados de teste
        nome = "Usuario de Teste"
        email = "teste@unittest.com"
        senha_plana = "senha123"
        cargo = "Testador"

        # Adição do usuário
        senha_hashed = db.hash_senha(senha_plana)
        try:
            self.cursor.execute(
                "INSERT INTO utilizadores (nome, email, senha, cargo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hashed, cargo)
            )
            self.conn.commit()
            # Se chegou aqui, a inserção funcionou
        except sqlite3.IntegrityError:
            self.fail("A inserção do usuário de teste falhou com IntegrityError. O teste não pode continuar.")

        # Busca do usuário (usando a mesma conexão)
        self.cursor.execute("SELECT * FROM utilizadores WHERE email = ?", (email,))
        usuario_encontrado_row = self.cursor.fetchone()

        # Asserções (Verificações)
        self.assertIsNotNone(usuario_encontrado_row, "A busca pelo usuário recém-adicionado retornou None.")

        # Convertendo sqlite3.Row para um dicionário para facilitar o acesso
        usuario_encontrado = dict(usuario_encontrado_row)

        self.assertEqual(usuario_encontrado['nome'], nome)
        self.assertEqual(usuario_encontrado['email'], email)

        # Verifica a senha do usuário encontrado
        self.assertTrue(db.verificar_senha(senha_plana, usuario_encontrado['senha']))


if __name__ == '__main__':
    unittest.main()