# src/main.py

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
        self._current_frame = None
        self.show_login_view()

    def switch_frame(self, frame_class, *args):
        if self._current_frame:
            self._current_frame.destroy()

        # A nova instância é criada passando 'self' como parent e controller
        self._current_frame = frame_class(self, self, *args)
        self._current_frame.pack(fill="both", expand=True)

    def show_login_view(self):
        self.geometry("400x550")
        self.resizable(False, False)
        # LoginView não precisa de argumentos extras
        self.switch_frame(LoginView)

    def show_main_view(self, user_name):
        self.geometry("1280x720")
        self.resizable(True, True)
        # Passa user_name como o argumento extra
        self.switch_frame(MainView, user_name)

    def show_register_view(self):
        self.geometry("400x550")
        self.resizable(False, False)
        # RegisterView não precisa de argumentos extras
        self.switch_frame(RegisterView)

    def navigate_to_vehicle_view_from_main(self):
        if isinstance(self._current_frame, MainView):
            self._current_frame.show_vehicle_view()
        else:
            logging.error("Tentativa de navegar para VehicleView sem a MainView estar ativa.")


if __name__ == "__main__":
    setup_logging()
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        logging.critical("Ocorreu um erro fatal e não capturado na aplicação!", exc_info=True)