import customtkinter as ctk
from backend import database as db
from frontend.vehicle_view import VehicleView


class MainView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Layout principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Frame menu lateral
        self.menu_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, rowspan=2, sticky="nsw")

        self.label_menu = ctk.CTkLabel(self.menu_frame, text="Luxury Wheels", font=("Arial", 20, "bold"))
        self.label_menu.grid(row=0, column=0, padx=20, pady=20)

        # Botões do menu
        self.btn_dashboard = ctk.CTkButton(self.menu_frame, text="Dashboard", command=self.show_dashboard_view)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_veiculos = ctk.CTkButton(self.menu_frame, text="Veículos", command=self.show_vehicle_view)
        self.btn_veiculos.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_clentes = ctk.CTKButton(self.menu_frame, text="Clentes", command=self.show_clentes_view)
        self.btn_clentes.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_reservas = ctk.CTkButton(self.menu_frame, text="Reservas", command=self.show_reservas_view)
        self.btn_reservas.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_logout = ctk.CTkButton(self.menu_frame, text="Logout", command=self.logout, fg_color="#c0392b",
                                        hover_color="#e74c3c")
        self.btn_logout.grid(row=5, column=0, padx=20, pady=20, sticky="sew")

        # Frame de conteúdo principal
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")

        # Inicia mostrando o dashboard (ou tela de boas vindas)
        self.show_dashboard_view()

    def show_view(self, view_class):
        # limpa o frame de conteudo
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        # Adiciona a nova visao
        view = view_class(self.content_frame, self.controller)
        view.pack(fill="both", expand=True)

    def show_dashboard_view(self):
        # Por enquanto tela de boas vindas
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        label = ctk.CTkLabel(self.content_frame, text="Dashboard de Business Intelligence", font=("Arial", 20, "bold"))
        label.pack(pady=100)

    def show_vehicle_view(self):
        self.show_view(VehicleView)

    def logout(self):
        self.controller.show_login_view()
