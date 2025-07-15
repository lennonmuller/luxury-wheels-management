import customtkinter as ctk
from .dashboard_view import DashboardView
from .vehicle_view import VehicleView
from .client_view import ClientView
from PIL import Image, ImageTk
import os

class MainView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Layout Principal ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Frame do Menu Lateral ---
        self.menu_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, rowspan=2, sticky="nsw")
        self.menu_frame.grid_rowconfigure(5, weight=1)

        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'assets',
                                 'logo.png')
        logo_image = ctk.CTkImage(Image.open(logo_path), size=(100, 50))  # Tamanho menor para o menu
        logo_label = ctk.CTkLabel(self.menu_frame, image=logo_image, text="")
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        #self.label_menu = ctk.CTkLabel(self.menu_frame, text="Luxury Wheels", font=("Arial", 20, "bold"))
        #self.label_menu.grid(row=1, column=0, padx=20, pady=(20, 10))

        self.label_welcome = ctk.CTkLabel(self.menu_frame, text="Bem-vindo(a)!", font=("Arial", 16))
        self.label_welcome.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="ew")

        # --- Botões do Menu ---
        self.btn_dashboard = ctk.CTkButton(self.menu_frame, text="Dashboard", command=self.show_dashboard_view)
        self.btn_dashboard.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_veiculos = ctk.CTkButton(self.menu_frame, text="Veículos", command=self.show_vehicle_view)
        self.btn_veiculos.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_clientes = ctk.CTkButton(self.menu_frame, text="Clientes", command=self.show_clientes_view)
        self.btn_clientes.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_logout = ctk.CTkButton(self.menu_frame, text="Logout", command=self.logout, fg_color="#c0392b",
                                        hover_color="#e74c3c")
        self.btn_logout.grid(row=6, column=0, padx=20, pady=20, sticky="sew")

        # --- Frame de Conteúdo Principal ---
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=0, column=1, rowspan=2, padx=20, pady=20, sticky="nsew")

        # Inicia mostrando o dashboard
        self.show_dashboard_view()

    def update_welcome_message(self, user_name):
        welcome_text = f"Bem-vindo(a),\n{user_name.split(' ')[0]}!"
        self.label_welcome.configure(text=welcome_text)
        self.show_dashboard_view()

    def show_view(self, view_class):
        # Limpa o frame de conteúdo
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        # Adiciona a nova visão
        view = view_class(self.content_frame, self.controller)
        view.pack(fill="both", expand=True)

    def show_dashboard_view(self):
        self.show_view(DashboardView)

    def show_vehicle_view(self):
        self.show_view(VehicleView)

    # NOVO: Placeholder para a função do botão de clientes
    def show_clientes_view(self):
        self.show_view(ClientView)

    def logout(self):
        self.controller.show_login_view()