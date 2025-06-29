# src/frontend/login_view.py

import customtkinter as ctk
from backend import database as db


class LoginView(ctk.CTkFrame):
    # Nível 0 de indentação (início da classe)

    def __init__(self, parent, controller):
        # Nível 1 de indentação (dentro da classe)
        super().__init__(parent)
        self.controller = controller

        # Todo o código aqui dentro está no Nível 2 de indentação (dentro do método __init__)
        self.label = ctk.CTkLabel(self, text="Login - Luxury Wheels", font=("Arial", 24, "bold"))
        self.label.pack(pady=20, padx=10)

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email", width=250)
        self.email_entry.pack(pady=10, padx=10)
        self.email_entry.bind("<Return>", self.fazer_login)

        self.senha_entry = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=250)
        self.senha_entry.pack(pady=10, padx=10)
        self.senha_entry.bind("<Return>", self.fazer_login)

        self.login_button = ctk.CTkButton(self, text="Entrar", command=self.fazer_login)
        self.login_button.pack(pady=20, padx=10)

        self.register_button = ctk.CTkButton(self, text="Criar Conta",
                                             command=self.controller.show_register_view,
                                             fg_color="transparent", border_width=1)
        self.register_button.pack(pady=5, padx=10)

        self.msg_label = ctk.CTkLabel(self, text="", text_color="red")
        self.msg_label.pack(pady=5, padx=10)

    # Este método está no Nível 1 de indentação (paralelo ao __init__)
    def fazer_login(self, event=None):
        # Todo este bloco de código está no Nível 2 de indentação (dentro do método fazer_login)
        email = self.email_entry.get()
        senha = self.senha_entry.get()

        if not email or not senha:
            # Nível 3 de indentação (dentro do if)
            self.msg_label.configure(text="Por favor, preencha todos os campos.")
            return  # Este return está corretamente dentro da função

        utilizador = db.buscar_utilizador_por_email(email)

        if utilizador and db.verificar_senha(senha, utilizador['senha']):
            # Nível 3 de indentação
            self.msg_label.configure(text="Login bem-sucedido!", text_color="green")
            self.controller.show_main_view()
        else:
            # Nível 3 de indentação
            self.msg_label.configure(text="Email ou senha incorretos.")