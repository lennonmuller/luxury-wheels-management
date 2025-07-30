import customtkinter as ctk
from tkinter import ttk, messagebox
from backend import database as db
from utils.helpers import parse_datestr_flexible
from datetime import datetime


class ReservationView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ctk.CTkLabel(self, text="Gestão de Reservas", font=("Arial", 24, "bold")).pack(pady=20)

        # Frame da Tabela
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Treeview
        columns = ("ID", "Cliente", "Veículo", "Placa", "Início", "Fim", "Status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(table_frame, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Botões
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(button_frame, text="Editar Reserva", command=self.abrir_editar_reserva).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Cancelar/Remover Reserva", command=self.cancelar_reserva, fg_color="#c0392b",
                      hover_color="#e74c3c").pack(side="left", padx=10)

        self.carregar_dados()

    def carregar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in db.listar_todas_reservas_detalhadas():
            inicio_f = parse_datestr_flexible(r['data_inicio']).strftime('%d/%m/%Y')
            fim_f = parse_datestr_flexible(r['data_fim']).strftime('%d/%m/%Y')
            veiculo = f"{r['marca']} {r['modelo']}"

            self.tree.insert("", "end", values=(
                r['reserva_id'], r['cliente_nome'], veiculo,
                r['placa'], inicio_f, fim_f, r['status'].title()
            ))

    def abrir_editar_reserva(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione uma reserva para editar.")
            return

        reserva_id = self.tree.item(selected_item)["values"][0]
        EditarReservaWindow(self, reserva_id)

    def cancelar_reserva(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione uma reserva para cancelar.")
            return

        reserva_id = self.tree.item(selected_item)["values"][0]

        if messagebox.askyesno("Confirmação", f"Tem a certeza que deseja cancelar/remover a reserva ID {reserva_id}?"):
            if db.deletar_reserva(reserva_id):
                messagebox.showinfo("Sucesso", "Reserva cancelada com sucesso.")
                self.carregar_dados()
            else:
                messagebox.showerror("Erro", "Não foi possível cancelar a reserva.")


class EditarReservaWindow(ctk.CTkToplevel):
    def __init__(self, parent, reserva_id):
        super().__init__(parent)
        self.parent_view = parent
        self.reserva_id = reserva_id

        reserva = db.buscar_reserva_por_id(self.reserva_id)

        self.title(f"Editar Reserva ID: {self.reserva_id}")
        self.geometry("400x300")
        self.grab_set()

        ctk.CTkLabel(self, text="Data de Início (DD/MM/AAAA):").pack(pady=(10, 0))
        self.data_inicio_entry = ctk.CTkEntry(self)
        self.data_inicio_entry.insert(0, parse_datestr_flexible(reserva['data_inicio']).strftime('%d/%m/%Y'))
        self.data_inicio_entry.pack()

        ctk.CTkLabel(self, text="Data de Fim (DD/MM/AAAA):").pack(pady=(10, 0))
        self.data_fim_entry = ctk.CTkEntry(self)
        self.data_fim_entry.insert(0, parse_datestr_flexible(reserva['data_fim']).strftime('%d/%m/%Y'))
        self.data_fim_entry.pack()

        ctk.CTkButton(self, text="Salvar Alterações", command=self.salvar).pack(pady=20)

    def salvar(self):
        inicio_str = self.data_inicio_entry.get()
        fim_str = self.data_fim_entry.get()

        try:
            inicio_db = datetime.strptime(inicio_str, '%d/%m/%Y').strftime('%Y-%m-%d %H:%M:%S')
            fim_db = datetime.strptime(fim_str, '%d/%m/%Y').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido. Use DD/MM/AAAA.")
            return

        sucesso, mensagem = db.atualizar_reserva(self.reserva_id, inicio_db, fim_db)

        if sucesso:
            messagebox.showinfo("Sucesso", mensagem)
            self.parent_view.carregar_dados()
            self.destroy()
        else:
            messagebox.showerror("Erro", mensagem)