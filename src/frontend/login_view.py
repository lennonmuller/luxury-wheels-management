import customtkinter as ctk
from backend import database as db #a ponte entre o frontend e o backend

class LoginView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        #widgets
        self.label = ctk.CTkLabel(self, text="Login - Luxury Wheels", font=("Arial", 24, "bold"))
        self.label.pack(pady=20, padx=10)

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email", width=250)
        self.email_entry.pack(pady=10, padx=10)

        self.senha_entry = ctk.CTkEntry(self, placeholder_text="Senha", show="*",width=250)
        self.senha_entry.pack(pady=10, padx=10)

        self.login_button = ctk.CTkButton(self, text="Entrar", command=self.fazer_login)
        self.login_button.pack(pady=20, padx=10)

        self.msg_label = ctk.CTkLabel(self, text="", text_color="red")
        self.msg_label.pack(pady=5, padx=10)

        #exemplo de dados para teste inicial
        # db.adicionar_utilizador("Admin", "admin@lw.com", "1234", "Gerente")

        def fazer_login(self):
            """Função chamada pelo botão de login."""
            email = self.email_entry.get()
            senha = self.senha_entry.get()

            if not email or not senha:
                self.msg_label.configure(text="Por favor, preencha todos os campos.")
                return

            #comunicação com backend
            utilizador = db.buscar_utilizador_por_email(email)

            if utilizador and db.verificar_senha(senha, utilizador['senha']):
                self.msg_label.configure(text="Login bem-sucedido!", text_color="green")
                # chama o método do controller para trocar de tela
                self.controller.show_main_view()
            else:
                self.msg_label.configure(text="Email ou senha incorretos.")

