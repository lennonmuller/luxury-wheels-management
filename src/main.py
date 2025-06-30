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

    def switch_frame(self, frame_class):
        if self._current_frame:
            self._current_frame.destroy()

        self._current_frame = frame_class(self, self)
        self._current_frame.pack(fill="both", expand=True)

    def show_login_view(self):
        self.geometry("400x450")
        self.resizable(False, False)
        # O uso de 'after' agenda a troca, evitando o TclError
        self.after(10, lambda: self.switch_frame(LoginView))

    def show_main_view(self):
        self.geometry("1200x700")
        self.resizable(True, True)
        self.after(10, lambda: self.switch_frame(MainView))

    def show_register_view(self):
        self.geometry("400x500")
        self.resizable(False, False)
        self.after(10, lambda: self.switch_frame(RegisterView))

    def show_client_view(self):
        self.geometry("400x500")
        self.resizable(False, False)
        self.after(10, lambda: self.switch_frame(ClientView))


if __name__ == "__main__":
    app = App()
    app.mainloop()
