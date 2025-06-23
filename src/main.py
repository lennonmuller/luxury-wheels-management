import customtkinter as ctk
from frontend.login_view import LoginView

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Luxury Wheels - Sistema de Gestão")
        self.geometry("400x450")
        self.resizable(False, False)

        # Container para trocar as telas
        self.container = ctk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)

        # iniciar com a tela de login
        self.show_login_view()

    def show_login_view(self):
        """Mostra a tela de login no container principal """
        #Limpa o container antes de adicionar uma nova tela
        for widget in self.container.winfo_children():
            widget.destroy()

        login_frame = LoginView(self.container, self)
        login_frame.pack(fill="both", expand=True)

    def show_main_view(self):
        """Futuramente, mostrará a tela principal (dashboard) após o login"""
        print("Login bem-sucedido! Navegando para a tela principal...")
        #aqui sera classe MainView quando estiver pronta

if __name__ == "__main__":
    app = App()
    app.mainloop()