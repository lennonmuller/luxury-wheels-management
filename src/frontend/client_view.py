from datetime import datetime, timedelta, date
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from backend import database as db
from PIL import Image
import os
from datetime import datetime, timedelta
import re
from utils.helpers import  parse_datestr_flexible
import pandas as pd


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
            frame.pack(padx=20, pady=(10, 0), fill="x", expand=True)
            label = ctk.CTkLabel(frame, text=f"{campo}:", width=150, anchor="w")
            label.pack(side="left")
            entry = ctk.CTkEntry(frame)
            entry.pack(side="left", fill="x", expand=True)

            if dados_cliente:
                # Normaliza o nome do campo para usar como chave (ex: "Nome Completo" -> "nome_completo")
                chave_coluna = campo.lower().replace(" ", "_").replace("nº_", "n").replace("_(cc)", "")
                if chave_coluna in dados_cliente:
                    entry.insert(0, dados_cliente[chave_coluna])

            self.entradas[campo.lower().replace(" ", "_").replace("nº_", "n").replace("_(cc)", "")] = entry

        texto_botao = "Confirmar Alterações" if dados_cliente else "Salvar Novo Cliente"
        self.btn_salvar = ctk.CTkButton(self, text=texto_botao, command=self.salvar)
        self.btn_salvar.pack(pady=20)

    def salvar(self):
        valores = {chave: entry.get() for chave, entry in self.entradas.items()}

        if not all(valores.values()):
            messagebox.showwarning("Atenção", "Por favor, preencha todos os campos!")
            return

        if self.dados_cliente:
            db.atualizar_cliente(self.dados_cliente['id'], **valores)
            messagebox.showinfo("Sucesso", "Dados do cliente atualizados!")
        else:  # Modo Adição
            if not db.adicionar_cliente(**valores):
                messagebox.showerror("Erro",
                                     "Erro ao adicionar cliente. Verifique se o NIF, Email ou CC já existem no sistema.")
                return
            messagebox.showinfo("Sucesso", "Novo cliente adicionado com sucesso!")

        self.parent_view.carregar_dados()
        self.destroy()


# --- CLASSE PARA A JANELA DE CRIAÇÃO DE RESERVA ---
class CriarReservaWindow(ctk.CTkToplevel):
    def __init__(self, parent, controller, id_cliente, nome_cliente):
        super().__init__(parent)
        self.parent_view = parent
        self.controller = controller
        self.id_cliente = id_cliente

        self.title(f"Nova Reserva para: {nome_cliente}")
        self.geometry("500x450")
        self.resizable(False, False)
        self.grab_set()

        # --- Widgets ---
        ctk.CTkLabel(self, text="Selecione um Veículo Disponível:").pack(padx=20, pady=(10, 0), anchor="w")

        veiculos_disponiveis = db.listar_veiculos_disponiveis()
        veiculo_nomes = [f"ID {v['id']}: {v['marca']} {v['modelo']} (Placa: {v['placa']})" for v in
                         veiculos_disponiveis]
        self.veiculos_map = {nome: v['id'] for nome, v in zip(veiculo_nomes, veiculos_disponiveis)}

        self.veiculo_combobox = ctk.CTkComboBox(self, values=veiculo_nomes, width=460)
        self.veiculo_combobox.pack(padx=20, pady=(0, 10))
        if not veiculo_nomes:
            self.veiculo_combobox.set("Nenhum veículo disponível!")
            self.veiculo_combobox.configure(state="disabled")

        ctk.CTkLabel(self, text="Data de Início (DD/MM/AAAA):").pack(padx=20, pady=(10, 0), anchor="w")
        self.data_inicio_entry = ctk.CTkEntry(self, placeholder_text=datetime.now().strftime('%d/%m/%Y'))
        self.data_inicio_entry.pack(padx=20, fill="x")

        ctk.CTkLabel(self, text="Data de Fim (DD/MM/AAAA):").pack(padx=20, pady=(10, 0), anchor="w")
        self.data_fim_entry = ctk.CTkEntry(self,
                                           placeholder_text=(datetime.now() + timedelta(days=7)).strftime('%d/%m/%Y'))
        self.data_fim_entry.pack(padx=20, fill="x")

        ctk.CTkLabel(self, text="Forma de Pagamento:").pack(padx=20, pady=(10, 0), anchor="w")
        formas_pagamento = [p['nome'] for p in db.listar_formas_pagamento()]
        self.pagamento_map = {nome: p['id'] for nome, p in zip(formas_pagamento, db.listar_formas_pagamento())}
        self.pagamento_combobox = ctk.CTkComboBox(self, values=formas_pagamento, width=460)
        self.pagamento_combobox.pack(padx=20)

        self.btn_salvar = ctk.CTkButton(self, text="Confirmar Reserva", command=self.salvar_reserva)
        self.btn_salvar.pack(pady=20)

    def salvar_reserva(self):
        # 1. Obter dados da UI
        veiculo_selecionado = self.veiculo_combobox.get()
        data_inicio_str = self.data_inicio_entry.get() or self.data_inicio_entry.cget("placeholder_text")
        data_fim_str = self.data_fim_entry.get() or self.data_fim_entry.cget("placeholder_text")
        pagamento_selecionado = self.pagamento_combobox.get()

        # 2. Validação inicial de campos vazios
        if not veiculo_selecionado or "Nenhum veículo" in veiculo_selecionado or not pagamento_selecionado:
            messagebox.showerror("Erro de Validação", "Por favor, selecione um veículo e uma forma de pagamento.")
            return

        id_veiculo = self.veiculos_map[veiculo_selecionado]
        id_pagamento = self.pagamento_map.get(pagamento_selecionado)

        # 3. Bloco de conversão e validação de data
        try:
            data_inicio_obj = datetime.strptime(data_inicio_str, '%d/%m/%Y')
            data_fim_obj = datetime.strptime(data_fim_str, '%d/%m/%Y')

            if data_fim_obj <= data_inicio_obj:
                messagebox.showerror("Erro de Lógica", "A data de fim deve ser posterior à data de início.")
                return

            # Formata para o padrão do banco de dados (com hora)
            data_inicio_db = data_inicio_obj.strftime('%Y-%m-%d 00:00:00')
            data_fim_db = data_fim_obj.strftime('%Y-%m-%d 23:59:59')
        except ValueError:
            messagebox.showerror("Erro de Formato", "Por favor, insira as datas no formato DD/MM/AAAA.")
            return

        # 4. Verificação de disponibilidade no backend
        if not db.verificar_disponibilidade_veiculo(id_veiculo, data_inicio_db, data_fim_db):
            messagebox.showerror("Conflito de Reserva",
                                 "Este veículo já está reservado e indisponível para o período selecionado.")
            return

        # 5. Se tudo estiver OK, adiciona a reserva
        sucesso = db.adicionar_reserva(
            id_cliente=self.id_cliente,
            id_veiculo=id_veiculo,
            id_forma_pagamento=id_pagamento,
            data_inicio=data_inicio_db,
            data_fim=data_fim_db
        )

        # 6. Feedback final ao usuário
        if sucesso:
            messagebox.showinfo("Sucesso", "Reserva criada com sucesso!")
            # Tenta recarregar a tela de veículos para refletir a mudança de status
            try:
                self.parent_view.master.master.show_vehicle_view()
            except Exception as e:
                logging.warning(f"Não foi possível recarregar a view de veículos automaticamente: {e}")
            self.destroy()
        else:
            messagebox.showerror("Erro Inesperado",
                                 "Não foi possível criar a reserva. Verifique os logs para mais detalhes.")


# --- CLASSE PARA A JANELA DE HISTÓRICO DE CLIENTE ---
class HistoricoClienteWindow(ctk.CTkToplevel):
    def __init__(self, parent, id_cliente, nome_cliente):
        super().__init__(parent)
        self.title(f"Histórico de {nome_cliente}")
        self.geometry("750x400")
        self.grab_set()

        reservas = db.buscar_reservas_por_cliente(id_cliente)

        if not reservas:
            ctk.CTkLabel(self, text="Este cliente não possui histórico de reservas.", font=("Arial", 16)).pack(pady=20)
            return

        textbox = ctk.CTkTextbox(self, state="normal", font=("Courier New", 12))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)

        header = f"{'VEÍCULO'.ljust(35)} | {'INÍCIO'.ljust(10)} | {'FIM'.ljust(10)} | STATUS\n"
        textbox.insert("end", header)
        textbox.insert("end", "=" * len(header) + "\n")

        hoje = datetime.now().date()

        for r in reservas:
            try:
                veiculo = f"{r['marca']} {r['modelo']} ({r['placa']})"

                # Tenta converter as datas
                inicio_obj = parse_datestr_flexible(r['data_inicio'])
                fim_obj = parse_datestr_flexible(r['data_fim'])

                # Formata para exibição
                inicio_f = inicio_obj.strftime('%d/%m/%Y')  # Formato de 4 dígitos no ano
                fim_f = fim_obj.strftime('%d/%m/%Y')

                status = r['status_reserva'].upper()

                # A lógica que usa as variáveis do 'try' deve estar DENTRO do 'try'
                if status == 'ATIVA' and fim_obj.date() >= hoje:
                    linha = f"-> {veiculo.ljust(27)} | {inicio_f.ljust(12)} | {fim_f.ljust(12)} | {status}\n"
                else:
                    linha = f"   {veiculo.ljust(27)} | {inicio_f.ljust(12)} | {fim_f.ljust(12)} | {status}\n"

                textbox.insert("end", linha)

                # Adiciona o bloco 'except' que estava faltando
            except (ValueError, TypeError, AttributeError) as e:
                # Se uma reserva tiver dados corrompidos, loga o erro e continua para a próxima
                logging.error(
                    f"Não foi possível processar a reserva ID {r.get('id', 'N/A')} para o histórico do cliente: {e}")
                continue  # Pula para a próxima iteração do loop

            textbox.configure(state="disabled")

# --- CLASSE PRINCIPAL DA VISÃO DE CLIENTES ---
class ClientView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ctk.CTkLabel(self, text="Gestão de Clientes", font=("Arial", 24, "bold")).pack(pady=10, padx=10)

        content_frame = ctk.CTkFrame(self)
        content_frame.pack(pady=10, padx=10, fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", borderwidth=0)
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", font=("Arial", 10, "bold"))
        style.map('Treeview', background=[('selected', '#22559b')])

        self.tree = ttk.Treeview(content_frame, columns=("ID", "Nome", "NIF", "Email", "Telefone", "CC"), show="headings")

        self.tree.heading("ID", text="ID", anchor="center")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.heading("Nome", text="Nome Completo")
        self.tree.column("Nome", width=250)
        self.tree.heading("NIF", text="NIF", anchor="center")
        self.tree.column("NIF", width=120, anchor="center")
        self.tree.heading("Email", text="Email")
        self.tree.column("Email", width=250)
        self.tree.heading("Telefone", text="Telefone")
        self.tree.column("Telefone", width=150)
        self.tree.heading("CC", text="CC- Nº Cartão Cidadão")
        self.tree.column("CC", width=150, anchor="center")

        self.tree.pack(pady=20, padx=10, fill="both", expand=True)

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkButton(button_frame, text="Adicionar", command=self.abrir_adicionar).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Editar", command=self.abrir_editar).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Remover", command=self.deletar_cliente, fg_color="#c0392b",
                      hover_color="#e74c3c").pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Importar Clientes (CSV)", command=self.importar_clientes).pack(side="left",
                                                                                                         padx=10)

        action_button_frame = ctk.CTkFrame(self)
        action_button_frame.pack(pady=(0, 10), padx=10, fill="x")
        ctk.CTkButton(action_button_frame, text="Ver Histórico de Reservas", command=self.ver_historico).pack(
            side="left", padx=10)
        ctk.CTkButton(action_button_frame, text="Criar Reserva para Cliente", command=self.abrir_criar_reserva,
                      fg_color="#1f6aa5", hover_color="#144870").pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Exportar Clientes (CSV)", command=self.exportar_clientes).pack(side="left",
                                                                                                         padx=10)

        self.carregar_dados()

    def carregar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        clientes = db.listar_clientes()
        for c in clientes:
            self.tree.insert("", "end", values=(c["id"], c["nome_completo"], c["nif"], c["email"], c["telefone"], c["cc"]))

    def abrir_adicionar(self):
        FormularioCliente(self, self.controller)

    def abrir_editar(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um cliente para editar.")
            return

        item_id = self.tree.item(selected_item)["values"][0]
        clientes = db.listar_clientes()
        dados_cliente = next((dict(c) for c in clientes if c['id'] == item_id), None)

        if dados_cliente:
            FormularioCliente(self, self.controller, dados_cliente)

    def deletar_cliente(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um cliente para remover.")
            return

        item_values = self.tree.item(selected_item)["values"]
        id_cliente = item_values[0]
        nome_cliente = item_values[1]

        titulo_confirmacao= "Confirmação de Exclusão"
        mensagem_confirmacao = f"Tem a certeza que deseja remover permanentemente o cliente:\n\n{nome_cliente} (ID: {id_cliente})?"

        if messagebox.askyesno(titulo_confirmacao, mensagem_confirmacao):
            if db.deletar_cliente(id_cliente):
                messagebox.showinfo("Sucesso", "Cliente removido com sucesso.")
                self.carregar_dados()
            else:
                messagebox.showerror("Erro",
                                     "Não foi possível remover o cliente. Verifique se ele possui um histórico de reservas.")

    def importar_clientes(self):
        caminho_arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo CSV de clientes",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        if not caminho_arquivo: return

        if not messagebox.askyesno("Confirmação",
                                   "Deseja importar os clientes deste arquivo? Dados duplicados (NIF, Email, CC) serão ignorados."):
            return

        sucessos, falhas, erros = db.importar_clientes_de_csv(caminho_arquivo)

        mensagem_final = f"Importação Concluída!\n\n- Clientes importados: {sucessos}\n- Linhas com erro/duplicadas: {falhas}"
        if erros:
            erros_preview = "\n".join(erros[:3])
            mensagem_final += f"\n\nExemplo de erros:\n{erros_preview}"

        messagebox.showinfo("Resultado da Importação", mensagem_final)
        self.carregar_dados()

    def ver_historico(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um cliente para ver o histórico.")
            return

        item_values = self.tree.item(selected_item)["values"]
        id_cliente, nome_cliente = item_values[0], item_values[1]

        HistoricoClienteWindow(self, id_cliente, nome_cliente)

    def abrir_criar_reserva(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um cliente para criar uma reserva.")
            return

        item_values = self.tree.item(selected_item)["values"]
        id_cliente, nome_cliente = item_values[0], item_values[1]

        CriarReservaWindow(self, self.controller, id_cliente, nome_cliente)

    def exportar_clientes(self):
        # 1. Busca os dados mais recentes do banco
        clientes = db.listar_clientes()
        if not clientes:
            messagebox.showinfo("Informação", "Não há clientes para exportar.")
            return

        # 2. Converte a lista de objetos 'Row' do SQLite para um formato que o Pandas entende bem
        dados_clientes = [dict(cliente) for cliente in clientes]
        df = pd.DataFrame(dados_clientes)

        # 3. Pede ao usuário para escolher onde salvar o arquivo
        caminho_arquivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")],
            title="Salvar lista de clientes como..."
        )

        if not caminho_arquivo:
            # O usuário clicou em "Cancelar"
            return

        # 4. Tenta exportar os dados para o arquivo CSV
        try:
            # Usamos sep=';' que é mais compatível com o Excel em configurações europeias
            # encoding='utf-8-sig' garante que caracteres especiais (acentos) funcionem bem
            df.to_csv(caminho_arquivo, index=False, sep=';', encoding='utf-8-sig')
            messagebox.showinfo("Sucesso", f"Lista de clientes exportada com sucesso para:\n{caminho_arquivo}")
        except Exception as e:
            logging.error(f"Erro ao exportar lista de clientes: {e}", exc_info=True)
            messagebox.showerror("Erro de Exportação", f"Ocorreu um erro ao salvar o arquivo: {e}")