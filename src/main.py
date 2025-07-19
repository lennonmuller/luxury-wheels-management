import customtkinter as ctk
from frontend.login_view import LoginView
from frontend.register_view import RegisterView
from frontend.main_view import MainView
from backend.logger_config import setup_logging
import logging

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Luxury Wheels - Sistema de Gestão")
        ctk.set_appearance_mode("dark")

        # Container principal onde todos os frames viverão
        container = ctk.CTkFrame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.current_user_name = "" # Para guardar o nome do usuário logado

        # Criar todas as telas uma vez e guardá-las no dicionário
        for F in (LoginView, MainView, RegisterView):
            frame_name = F.__name__
            frame = F(container, self) # Passa o container e o controller
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Inicia mostrando a tela de login
        self.show_frame("LoginView")

    def show_frame(self, frame_name):
        """Levanta o frame desejado para a frente."""
        if frame_name == "MainView":
            # Redimensiona a janela para a tela principal
            self.geometry("1200x700")
            self.resizable(True, True)
            # ATUALIZA A MENSAGEM DE BOAS-VINDAS ANTES DE MOSTRAR
            main_frame = self.frames["MainView"]
            main_frame.update_welcome_message(self.current_user_name)
        else:
            # Redimensiona para as telas de auth
            self.geometry("400x500")
            self.resizable(False, False)

        frame = self.frames[frame_name]
        frame.tkraise()

    # Mantenha os métodos de conveniência para serem chamados de outras views
    def show_login_view(self):
        self.show_frame("LoginView")

    def show_main_view(self, user_name="Usuário"):
        self.current_user_name = user_name # Salva o nome do usuário
        self.show_frame("MainView")

    def show_register_view(self):
        self.show_frame("RegisterView")

if __name__ == "__main__":
    setup_logging()
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        logging.critical("Ocorreu um erro fatal na aplicação!", exc_info=True)