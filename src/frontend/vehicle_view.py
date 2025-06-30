import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
from backend import database as db


# classe para o formulario de adicionar/editar
class FormularioVeiculo(ctk.CTkToplevel):
    def __init__(self, parent, controller, dados_veiculo=None):
        super().__init__(parent)
        self.controller = controller
        self.parent_view = parent
        self.dados_veiculo = dados_veiculo

        self.title("Editar Veiculo" if dados_veiculo else "Adicionar Veiculo")
        self.geometry("400x550")
        self.resizable(width=False, height=False)
        self.grab_set()  # mantem o foco na janela

        self.campos = ["Marca", "Modelo", "Ano", "Placa", "Cor", "Valor Diaria", "Data Proxima Revisao"]
        self.entradas = {}

        for i, campo in enumerate(self.campos):
            label = ctk.CTkLabel(self, text=campo)
            label.pack(padx=20, pady=(10, 0), anchor="w")
            entry = ctk.CTkEntry(self, width=360)
            entry.pack(padx=20, pady=(0, 10), fill="x")

            if dados_veiculo:
                chave_coluna = campo.lower().replace(" ", "_")
                entry.insert(0, dados_veiculo[chave_coluna])

            self.entradas[campo.lower().replace(" ", "_")] = entry

        self.btn_salvar = ctk.CTkButton(self, text="Salvar", command=self.salvar)
        self.btn_salvar.pack(pady=20)

    def salvar(self):
        valores = {chave: entry.get() for chave, entry in self.entradas.items()}

        if not all(valores.values()):
            messagebox.showwarning("Atenção", "Preencha todos os campos!")
            return

        try:
            # Validação simples
            valores['ano'] = int(valores['ano'])
            valores['valor_diaria'] = float(valores['valor_diaria'])
        except ValueError:
            messagebox.showerror("Erro", "Ano e Valor da Diária devem ser números")
            return

        if self.dados_veiculo:  # modo edição
            db.adicionar_veiculo(self.dados_veiculo['id'], **valores)
        else:  # modo adição
            db.adicionar_veiculo(**valores)

            self.parent_view.carregar_dados()  # Atualiza a tabela na tela principal
            self.destroy()  # Fecha a tabela do formulário


class VehicleView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.label = ctk.CTkLabel(self, text="Gestão de Veículos", font=("Arial", 24, "bold"))
        self.label.pack(pady=10, padx=10)

        # frame oara a tabela e botoes
        content_frame = ttk.Frame(self)
        content_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Tabela (treeview)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", borderwidth=0)
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", font=("Arial", 10, "bold"))
        style.map('Treeview', background=[('selected', '#22559b')])

        self.tree = ttk.Treeview(content_frame,
                                 columns=("ID", "Marca", "Modelo", "Ano", "Placa", "Status", "Valor Diária"),
                                 show="headings")

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        self.tree.pack(pady=20, padx=10, fill="both", expand=True)

        # Botões
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkButton(button_frame, text="Adicionar", command=self.abrir_adicionar).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Editar", command=self.abrir_editar).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Remover", command=self.deletar_veiculo, fg_color="#c0392b",
                      hover_color="#e74c3c").pack(side="left", padx=10)

        self.carregar_dados()

    def carregar_dados(self):
        # limpa a tabela
        for item in self.tree.get_children():
            self.tree.delete(item)

        veiculos = db.listar_veiculos()
        # Carrega os dados do banco
        for v in veiculos:
            valor_formatado = f"$ {v['valor_diaria']:.2f}".replace('.', ',')
            self.tree.insert("", "end", values=(v["id"], v["marca"], v["modelo"], v["ano"], v["placa"], v["status"], valor_formatado))

    def abrir_adicionar(self):
        FormularioVeiculo(self, self.controller)

    def abrir_editar(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um veículo para editar.")
            return

        item_id = self.tree.item(selected_item)["values"][0]

        # Buscar todos os dados do veiculo, nao apenas os da tabela
        veiculos = db.listar_veiculos()
        dados_veiculo = next((v for v in veiculos if v['id'] == item_id), None)

        if dados_veiculo:
            FormularioVeiculo(self, self.controller, dados_veiculo)

    def deletar_veiculo(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um veículo para remover.")
            return
        id_veiculo = self.tree.item(selected_item)["values"][0]
        if messagebox.askyesno("Confirmação", f"Tem certeza que deseja remover o veículo ID {id_veiculo}?"):
            db.deletar_veiculo(id_veiculo)
            self.carregar_dados()
