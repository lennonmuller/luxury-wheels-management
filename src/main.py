import customtkinter as ctk
from frontend.login_view import LoginView
from frontend.register_view import RegisterView
from frontend.main_view import MainView
from src.frontend.client_view import ClientView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Luxury Wheels - Sistema de Gestão")
        self.geometry("1200x700")
        self.resizable(True, True)
        ctk.set_appearance_mode("dark")

        self._current_frame = None
        self.show_login_view()

    def switch_frame(self, frame_factory):
        if self._current_frame:
            self._current_frame.destroy()

        self._current_frame = frame_factory(self, self)
        self._current_frame.pack(fill="both", expand=True)

    def show_login_view(self):
        self.geometry("400x450")
        self.resizable(False, False)
        # O uso de 'after' agenda a troca, evitando o TclError
        self.switch_frame(lambda parent, controller: LoginView(parent, controller))

    def show_main_view(self, user_name="Usuário"):
        self.geometry("1200x700")
        self.resizable(True, True)
        self.switch_frame(lambda parent, controller: MainView(parent, controller, user_name))

    def show_register_view(self):
        self.geometry("400x500")
        self.resizable(False, False)
        self.switch_frame(lambda parent, controller: LoginView(parent, controller))

    def show_client_view(self):
        self.geometry("400x500")
        self.resizable(False, False)
        self.after(10, lambda: self.switch_frame(ClientView))


if __name__ == "__main__":
    app = App()
    app.mainloop()
