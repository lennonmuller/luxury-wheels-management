# src/frontend/register_view.py

import customtkinter as ctk
from backend import database as db


class RegisterView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Widgets ---
        self.label = ctk.CTkLabel(self, text="Crie sua Conta", font=("Arial", 24, "bold"))
        self.label.pack(pady=20, padx=10)

        self.nome_entry = ctk.CTkEntry(self, placeholder_text="Nome Completo", width=250)
        self.nome_entry.pack(pady=10, padx=10)

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email", width=250)
        self.email_entry.pack(pady=10, padx=10)

        self.senha_entry = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=250)
        self.senha_entry.pack(pady=10, padx=10)

        self.cargo_entry = ctk.CTkEntry(self, placeholder_text="Cargo (Ex: Gerente)", width=250)
        self.cargo_entry.pack(pady=10, padx=10)

        self.register_button = ctk.CTkButton(self, text="Registrar", command=self.registrar_usuario)
        self.register_button.pack(pady=20, padx=10)

        self.back_button = ctk.CTkButton(self, text="Voltar para Login",
                                         command=self.voltar_login,
                                         fg_color="transparent", border_width=1)
        self.back_button.pack(pady=5, padx=10)

        self.msg_label = ctk.CTkLabel(self, text="", text_color="red")
        self.msg_label.pack(pady=5, padx=10)

    def registrar_usuario(self):
        nome = self.nome_entry.get()
        email = self.email_entry.get()
        senha = self.senha_entry.get()
        cargo = self.cargo_entry.get()

        if not nome or not email or not senha or not cargo:
            self.msg_label.configure(text="Por favor, preencha todos os campos.", text_color="red")
            return

        if db.buscar_utilizador_por_email(email):
            self.msg_label.configure(text="Este email já está registrado.", text_color="red")
            return

        # Tenta adicionar o utilizador
        sucesso = db.adicionar_utilizador(nome, email, senha, cargo)

        if sucesso:
            self.msg_label.configure(text="Usuário registrado com sucesso!\nRedirecionando para o login...",
                                     text_color="green")

            # NOVO: Desabilita o botão para evitar cliques múltiplos
            self.register_button.configure(state="disabled")
            self.back_button.configure(state="disabled")

            # NOVO: Agenda a função _redirect_to_login para ser chamada após 2000ms (2 segundos)
            self.after(2000, self._redirect_to_login)
        else:
            # Caso raro, se houver outro erro no DB
            self.msg_label.configure(text="Ocorreu um erro ao registrar. Tente novamente.", text_color="red")

    # NOVO: Método privado para limpar e redirecionar
    def _redirect_to_login(self):
        # Limpa todos os campos de entrada
        self.nome_entry.delete(0, 'end')
        self.email_entry.delete(0, 'end')
        self.senha_entry.delete(0, 'end')
        self.cargo_entry.delete(0, 'end')

        # Chama o controller para trocar a tela
        self.controller.show_login_view()

    def voltar_login(self):
        # Limpa a mensagem de erro antes de voltar
        self.msg_label.configure(text="")
        self.controller.show_login_view()