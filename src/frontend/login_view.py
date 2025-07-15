
import customtkinter as ctk
from backend import database as db
from backend import config_manager as cfg
from PIL import Image
import os


class LoginView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'assets', 'logo.png')

        logo_image = ctk.CTkImage(light_image=Image.open(logo_path),
                                  dark_image=Image.open(logo_path),
                                  size=(100, 50))

        # Widget para exibir a imagem
        logo_label = ctk.CTkLabel(self, image=logo_image, text="")
        logo_label.pack(pady=(40, 20))
        self.label = ctk.CTkLabel(self, text="Login - Luxury Wheels", font=("Arial", 24, "bold"))
        self.label.pack(pady=20, padx=10)

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email", width=250)
        self.email_entry.pack(pady=10, padx=10)
        self.email_entry.bind("<Return>", self.fazer_login)

        self.senha_entry = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=250)
        self.senha_entry.pack(pady=10, padx=10)
        self.senha_entry.bind("<Return>", self.fazer_login)

        self.lembrar_var = ctk.StringVar(value="off")
        self.lembrar_checkbox = ctk.CTkCheckBox(self, text="Lembrar-me", variable=self.lembrar_var, onvalue="on", offvalue="off")
        self.lembrar_checkbox.pack(pady=5, padx=10)

        self.login_button = ctk.CTkButton(self, text="Entrar", command=self.fazer_login)
        self.login_button.pack(pady=20, padx=10)

        self.register_button = ctk.CTkButton(self, text="Criar Conta",
                                             command=self.controller.show_register_view,
                                             fg_color="transparent", border_width=1)
        self.register_button.pack(pady=5, padx=10)

        self.msg_label = ctk.CTkLabel(self, text="", text_color="red")
        self.msg_label.pack(pady=5, padx=10)

        self.preencher_email_lembrado()

    def preencher_email_lembrado(self):
        """Verifica se há um email salvo e o insere no campo de entrada."""
        email_salvo = cfg.obter_email_lembrado()
        if email_salvo:
            self.email_entry.insert(0, email_salvo)
            self.lembrar_var.set("on") #deixa a caixa marcada se houver email salvo

    def fazer_login(self, event=None):
        email = self.email_entry.get()
        senha = self.senha_entry.get()

        if not email or not senha:
            self.msg_label.configure(text="Por favor, preencha todos os campos.")
            return

        if self.lembrar_var.get() == "on":
            cfg.salvar_email_lembrado(email)
        else:
            cfg.limpar_email_lembrado()

        utilizador = db.buscar_utilizador_por_email(email)

        if utilizador and db.verificar_senha(senha, utilizador['senha']):
            self.msg_label.configure(text="Login bem-sucedido!", text_color="green")
            self.controller.show_main_view(utilizador['nome'])

        else:
            self.msg_label.configure(text="Email ou senha incorretos.")