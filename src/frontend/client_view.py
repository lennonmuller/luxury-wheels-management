from datetime import datetime, timedelta, date

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from backend import database as db


class FormularioCliente(ctk.CTkToplevel):
    def __init__(self, parent, controller, dados_cliente=None):
        super().__init__(parent)
        self.controller = controller
        self.parent_view = parent
        self.dados_cliente = dados_cliente

        self.title("Editar Cliente" if dados_cliente else "Adicionar Cliente")
        self.geometry("400x450")
        self.resizable(width=False, height=False)
        self.grab_set()

        self.campos = ["Nome Completo", "Email", "Telefone", "NIF", "CC"]
        self.entradas = {}

        for campo in self.campos:
            frame = ctk.CTkFrame(self)
            frame.pack(padx=20, pady=(10, 0), fill="x")
            label = ctk.CTkLabel(frame, text=campo, width=100, anchor="w")
            label.pack(side="left")
            entry = ctk.CTkEntry(frame)
            entry.pack(side="left", fill="x", expand=True)

            if dados_cliente:
                chave_coluna = campo.lower().replace(" ", "_")
                entry.insert(0, dados_cliente[chave_coluna])


            self.entradas[campo.lower().replace(" ", "_")] = entry

        self.btn_salvar = ctk.CTkButton(self, text="Salvar", command=self.salvar)
        self.btn_salvar.pack(pady=20)

    def salvar(self):
        valores = {chave: entry.get() for chave, entry in self.entradas.items()}

        if not all(valores.values()):
            messagebox.showwarning("Atenção", "Preencha todos os campos!")
            return

        if self.dados_cliente:
            db.atualizar_cliente(self.dados_cliente['id'], **valores)
        else:
            if not db.adicionar_cliente(**valores):
                messagebox.showerror("Erro", "Erro ao adicionar cliente. Verifique se o NIF, Email ou CC já existem.")
                return


        self.parent_view.carregar_dados()
        self.destroy()


class ClientView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.label = ctk.CTkLabel(self, text="Gestão de Clientes", font=("Arial", 24, "bold"))
        self.label.pack(pady=10)

        content_frame = ttk.Frame(self)
        content_frame.pack(pady=10, padx=10, fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white",
                        fieldbackground="#2a2d2e", borderwidth=0)
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", font=("Arial", 10, "bold"))
        style.map('Treeview', background=[('selected', '#22559b')])

        self.tree = ttk.Treeview(content_frame,
                                 columns=("ID", "Nome", "Email", "Telefone", "NIF", "CC"),
                                 show="headings")

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        self.tree.pack(pady=20, padx=10, fill="both", expand=True)

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkButton(button_frame, text="Adicionar", command=self.abrir_adicionar).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Editar", command=self.abrir_editar).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Remover", command=self.deletar_cliente, fg_color="#c0392b",
                      hover_color="#e74c3c").pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Ver Histórico", command=self.ver_historico).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Importar Clientes (CSV)", command=self.importar_clientes).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Criar Reserva", command=self.abrir_criar_reserva, fg_color="#1f6aa5", hover_color="#144870").pack(side="right", padx=10)

        self.carregar_dados()

    def carregar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        clientes = db.listar_clientes()
        for c in clientes:
            self.tree.insert("", "end", values=(c["id"], c["nome_completo"], c["email"], c["telefone"], c["nif"], c["cc"]))

    def abrir_adicionar(self):
        FormularioCliente(self, self.controller)

    def abrir_editar(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um cliente para editar.")
            return

        item_id = self.tree.item(selected_item)["values"][0]
        clientes = db.listar_clientes()
        dados_cliente = next((c for c in clientes if c['id'] == item_id), None)

        if dados_cliente:
            FormularioCliente(self, self.controller, dados_cliente)

    def deletar_cliente(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um cliente para remover.")
            return
        id_cliente = self.tree.item(selected_item)["values"][0]
        if messagebox.askyesno("Confirmação", f"Tem certeza que deseja remover o cliente ID {id_cliente}?"):
            db.deletar_cliente(id_cliente)
            self.carregar_dados()

    def ver_historico(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um cliente para ver historico.")
            return

        item_values = self.tree.item(selected_item)["values"]
        id_cliente = item_values[0]
        nome_cliente = item_values[1]

        #Chama uma nova janela para exibir histórico
        HistoricoClienteWindow(self, id_cliente, nome_cliente)

    def importar_clientes(self):
        caminho_arquivo = filedialog.askopenfilename(title="Selecione o arquivo CSV de clientes", filetypes=[("Arquivos CSV", "*.csv")])
        if not caminho_arquivo: return

        if not messagebox.askyesno("Confirmação", "Deseja importar os cliente desse arquivo? Dados duplicados (NIF, Email, CC) serão ignorados."):
            return

        sucessos, falhas, erros = db.importar_clientes_de_csv(caminho_arquivo)

        mensagem_final = f"Importação Concluída!\n\n- Clientes importados: {sucessos}\n- Linhas com Erro/duplicadas: {falhas}"
        if erros:
            erros_preview = "\n".join(erros[:3])
            mensagem_final = f"\n\nExemplo de erros:\n{erros_preview}"

        messagebox.showinfo("Resultado da Importação", mensagem_final)
        self.carregar_dados()

    def abrir_criar_reserva(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um cliente para criar uma reserva.")
            return

        item_values = self.tree.item(selected_item)["values"]
        id_cliente = item_values[0]
        nome_cliente = item_values[1]

        CriarReservaWindow(self, self.controller, id_cliente, nome_cliente)


class HistoricoClienteWindow(ctk.CTkToplevel):
    def __init__(self, parent, id_cliente, nome_cliente):
        super().__init__(parent)
        self.title(f"Histórico de {nome_cliente}")
        self.geometry("700x400")
        self.grab_set()

        reservas = db.buscar_reservas_por_cliente(id_cliente)

        if not reservas:
            ctk.CTkLabel(self, text="Este cliente não possui histórico de reservas.", font=("Arial", 16)).pack(pady=20)
            return

        textbox = ctk.CTkTextbox(self, state="normal", font=("Courier New", 12))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)

        textbox.insert("end", f"{'VEÍCULO'.ljust(30)} | {'INÍCIO'.ljust(12)} | {'FIM'.ljust(12)} | STATUS\n")
        textbox.insert("end", "=" * 70 + "\n")

        hoje = datetime.now().date()

        for r in reservas:
            veiculo = f"{r['marca']} {r['modelo']} ({r['placa']})"

            try:
                data_inicio_obj = datetime.strptime(r['data_inicio'], '%Y-%m-%d %H:%M:%S')
                data_fim_obj = datetime.strptime(r['data_fim'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data_inicio_obj = datetime.strptime(r['data_inicio'], '%Y-%m-%d')
                data_fim_obj = datetime.strptime(r['data_fim'], '%Y-%m-%d')

            inicio_str = data_inicio_obj.strftime('%d/%m/%y')
            fim_str = data_fim_obj.strftime('%d/%m/%y')

            status = r['status_reserva'].upper()

            if status == 'ATIVA' and data_fim_obj.date() >= hoje:
                linha = f"-> {veiculo.ljust(27)} | {inicio_str.ljust(12)} | {fim_str.ljust(12)} | {status}\n"
            else:
                linha = f"   {veiculo.ljust(27)} | {inicio_str.ljust(12)} | {fim_str.ljust(12)} | {status}\n"

            textbox.insert("end", linha)

        textbox.configure(state="disabled")


class CriarReservaWindow(ctk.CTkToplevel):
    def __init__(self, parent, controller, id_cliente, nome_cliente):
        super().__init__(parent)
        self.parent_view = parent
        self.controller = controller
        self.id_cliente = id_cliente

        self.title(f"Criar Reserva para: {nome_cliente}")
        self.geometry("500x550")
        self.grab_set()

        #Widgets
        ctk.CTkLabel(self, text="Selecione um veículo disponível:").pack(padx=20, pady=(10,0), anchor="w")

        veiculos_disponiveis = db.listar_veiculos_disponiveis()
        veiculos_nomes = [f"ID {v['id']}: {v['marca']}, {v['modelo']} (Placa: {v['placa']})" for v in veiculos_disponiveis]
        self.veiculos_map = {nome: v['id'] for nome, v in zip(veiculos_nomes, veiculos_disponiveis)}

        self.veiculo_combobox = ctk.CTkComboBox(self, values=veiculos_nomes, width=460)
        self.veiculo_combobox.pack(padx=20, pady=(0, 10))
        if not veiculos_nomes:
            self.veiculo_combobox.set("Nenhum veículo disponível!")
            self.veiculo_combobox.configure(state="disabled")

        ctk.CTkLabel(self, text="Data de Início (AAAA-MM-DD):").pack(padx=20, pady=(10, 0), anchor="w")
        self.data_inicio_entry = ctk.CTkEntry(self, placeholder_text=datetime.now().strftime('%Y-%m-%d'))
        self.data_inicio_entry.pack(padx=20)

        ctk.CTkLabel(self, text="Data de Fim (AAAA-MM-DD):").pack(padx=20, pady=(10, 0), anchor="w")
        self.data_fim_entry = ctk.CTkEntry(self,
                                           placeholder_text=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
        self.data_fim_entry.pack(padx=20)

        # Forma de Pagamento
        ctk.CTkLabel(self, text="Forma de Pagamento:").pack(padx=20, pady=(10, 0), anchor="w")
        formas_pagamento = [f"{p['nome']}" for p in db.listar_formas_pagamento()]
        self.pagamento_map = {nome: p['id'] for nome, p in zip(formas_pagamento, db.listar_formas_pagamento())}
        self.pagamento_combobox = ctk.CTkComboBox(self, values=formas_pagamento, width=460)
        self.pagamento_combobox.pack(padx=20)

        # Botão Salvar
        self.btn_salvar = ctk.CTkButton(self, text="Confirmar Reserva", command=self.salvar_reserva)
        self.btn_salvar.pack(pady=20)

    def salvar_reserva(self):
        veiculo_selecionado = self.veiculo_combobox.get()
        if not veiculo_selecionado or veiculo_selecionado == "Nenhum veículo disponível!":
            messagebox.showerror("Erro", "Nenhum veículo selecionado.")
            return

        id_veiculo = self.veiculos_map[veiculo_selecionado]
        data_inicio = self.data_inicio_entry.get() or self.data_inicio_entry.cget("placeholder_text")
        data_fim = self.data_fim_entry.get() or self.data_fim_entry.cget("placeholder_text")
        pagamento_selecionado = self.pagamento_combobox.get()
        id_pagamento = self.pagamento_map.get(pagamento_selecionado)

        # Validação
        try:
            datetime.strptime(data_inicio, '%Y-%m-%d')
            datetime.strptime(data_fim, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Erro de Formato", "Por favor, insira as datas no formato AAAA-MM-DD.")
            return

        sucesso = db.adicionar_reserva(
            id_cliente=self.id_cliente,
            id_veiculo=id_veiculo,
            id_forma_pagamento=id_pagamento,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        if sucesso:
            messagebox.showinfo("Sucesso", "Reserva criada com sucesso!")
            self.parent_view.master.master.show_vehicle_view()  # Força a atualização da tela de veículos
            self.destroy()
        else:
            messagebox.showerror("Erro", "Não foi possível criar a reserva. O veículo pode não estar mais disponível.")