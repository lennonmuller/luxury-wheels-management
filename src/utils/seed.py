# src/utils/seed.py

import os
import sys

# Adiciona o diretório raiz do projeto ao path para que possamos importar o backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.backend import database as db


def povoar_banco():
    """
    Popula o banco de dados com dados iniciais para teste.
    Esta função pode ser executada com segurança múltiplas vezes.
    """
    print("Iniciando povoamento do banco de dados...")

    # --- Adicionar Formas de Pagamento ---
    formas_pagamento = ["Cartão de Crédito", "PIX", "Dinheiro", "Transferência Bancária"]
    print("Adicionando formas de pagamento...")
    with db.conectar_bd() as conn:
        cursor = conn.cursor()
        for forma in formas_pagamento:
            # Verifica se já existe para não duplicar
            cursor.execute("SELECT id FROM formas_pagamento WHERE nome = ?", (forma,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO formas_pagamento (nome) VALUES (?)", (forma,))
                print(f"  - {forma} adicionado.")
        conn.commit()

    # --- Adicionar Utilizadores ---
    print("\nAdicionando utilizadores...")
    # A função adicionar_utilizador já verifica se o email existe, então não precisamos checar aqui.
    if db.adicionar_utilizador("Marco Aurélio", "admin@lw.com", "admin123", "Gerente"):
        print("  - Utilizador 'Gerente' (admin@lw.com / senha: admin123) criado.")

    if db.adicionar_utilizador("Carlos Atendente", "user@lw.com", "user123", "Atendente"):
        print("  - Utilizador 'Atendente' (user@lw.com / senha: user123) criado.")

    # --- Adicionar Veículos ---
    print("\nAdicionando veículos...")
    veiculos = [
        ('BMW', 'X6', 2023, 'BMW-2023', 'Preto', 850.00, '2024-12-01'),
        ('Mercedes-Benz', 'C-Class', 2022, 'MRC-2022', 'Branco', 700.50, '2024-11-15'),
        ('Audi', 'Q5', 2023, 'AUD-2023', 'Cinza', 780.00, '2025-02-10'),
        ('Porsche', '911 Carrera', 2021, 'PRH-2021', 'Amarelo', 1500.00, '2024-10-25'),
    ]

    with db.conectar_bd() as conn:
        cursor = conn.cursor()
        for v in veiculos:
            cursor.execute("SELECT id FROM veiculos WHERE placa = ?", (v[3],))
            if cursor.fetchone() is None:
                db.adicionar_veiculo(*v)  # O '*' desempacota a tupla nos argumentos da função
                print(f"  - Veículo {v[0]} {v[1]} (Placa: {v[3]}) adicionado.")

    print("\nPovoamento concluído com sucesso!")


if __name__ == "__main__":
    # Remove o banco de dados antigo para garantir um estado limpo, se desejar.
    # CUIDADO: Isso apaga todos os dados existentes.
    # if os.path.exists(db.DB_PATH):
    #     os.remove(db.DB_PATH)
    #     print("Banco de dados antigo removido.")

    # É necessário recriar as tabelas se o arquivo for removido
    # Aqui, vamos assumir que as tabelas já existem e apenas adicionar os dados.
    povoar_banco()
