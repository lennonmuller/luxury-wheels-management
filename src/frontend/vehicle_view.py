import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
from backend import database as db
import pandas as pd
from tkinter import filedialog



# classe para o formulario de adicionar/editar
class FormularioVeiculo(ctk.CTkToplevel):
    def __init__(self, parent, controller, dados_veiculo=None):
        super().__init__(parent)
        self.controller = controller
        self.parent_view = parent
        self.dados_veiculo = dados_veiculo

        self.title("Editar Veiculo" if dados_veiculo else "Adicionar Veiculo")
        self.geometry("400x600")
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
            valores['valor_diaria'] = float(valores['valor_diaria'].replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Ano e Valor da Diária devem ser números")
            return

        if self.dados_veiculo:  # modo edição
            db.atualizar_veiculo(self.dados_veiculo['id'], **valores)
            messagebox.showinfo("Sucesso", "Veículo atualizado com sucesso!")
        else:  # modo adição
            db.adicionar_veiculo(**valores)
            messagebox.showinfo("Sucesso", "Novo veículo adicionado a frota!")

            self.parent_view.carregar_dados()  # Atualiza a tabela na tela principal
            self.destroy()  # Fecha a tabela do formulário


class HistoricoVeiculoWindow(ctk.CTkToplevel):
    def __init__(self, parent, id_veiculo, nome_veiculo):
        super().__init__(parent)
        self.title(f"Histórico de Aluguel - {nome_veiculo}")
        self.geometry("700x400")
        self.grab_set()

        reservas = db.buscar_reservas_por_veiculo(id_veiculo)

        if not reservas:
            ctk.CTkLabel(self, text="Este veículo não possui histórico de aluguéis.", font=("Arial", 16)).pack(pady=20)
            return

        textbox = ctk.CTkTextbox(self, state="normal", font=("Courier New", 12))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)

        textbox.insert("end", f"{'CLIENTE'.ljust(30)} | {'NIF'.ljust(15)} | {'INÍCIO'.ljust(12)} | {'FIM'.ljust(12)}\n")
        textbox.insert("end", "=" * 75 + "\n")

        for r in reservas:
            cliente = r['nome_completo']
            nif = r['nif']

            try:
                inicio = datetime.strptime(r['data_inicio'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%y')
                fim = datetime.strptime(r['data_fim'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%y')
            except (ValueError, TypeError):
                inicio = str(r['data_inicio'])
                fim = str(r['data_fim'])

            linha = f"{cliente.ljust(30)} | {nif.ljust(15)} | {inicio.ljust(12)} | {fim.ljust(12)}\n"
            textbox.insert("end", linha)

        textbox.configure(state="disabled")

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

        self.tree.tag_configure('devolucao_hoje', background='#5D4037', foreground='white')
        self.tree.tag_configure('manutencao', background='#4A148C', foreground='white')  # Exemplo para outra cor

        self.tree.pack(pady=20, padx=10, fill="both", expand=True)

        # Botões
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkButton(button_frame, text="Adicionar", command=self.abrir_adicionar).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Editar", command=self.abrir_editar).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Remover", command=self.deletar_veiculo, fg_color="#c0392b",
                      hover_color="#e74c3c").pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Exportar para Excel", command=self.exportar_para_excel).pack(side="right", padx=10)
        ctk.CTkButton(button_frame, text="Ver Histórico", command=self.ver_historico).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Importar Frota (CSV)", command=self.importar_frota).pack(side="left", padx=10)


        self.carregar_dados()

    def carregar_dados(self):
        # limpa a tabela
        for item in self.tree.get_children():
            self.tree.delete(item)

        veiculos_devolucao_hoje = db.buscar_veiculos_com_devolucao_hoje()
        veiculos = db.listar_veiculos()

        for v in veiculos:
            tag = ''  # Tag padrão
            if v['status'] == 'manutenção':
                tag = 'manutencao'
            elif v['id'] in veiculos_devolucao_hoje:
                tag = 'devolucao_hoje'

            # Formatação dos valores para exibição
            valor_formatado = f"R$ {v['valor_diaria']:.2f}"
            status_formatado = v['status'].capitalize()

            self.tree.insert("", "end", values=(
                v["id"], v["marca"], v["modelo"], v["ano"], v["placa"], status_formatado, valor_formatado
            ), tags=(tag,))

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

    def exportar_para_excel(self):
        veiculos = db.listar_veiculos()
        if not veiculos:
            messagebox.showinfo("Informação", "Não há veículos para exportar.")
            return

        dados_veiculos = [dict(veiculo) for veiculo in veiculos]

        df = pd.DataFrame(dados_veiculos)

        #Abrir caixa de dialogo para o usuário escolher onde salvar

        caminho_arquivo = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("Todos os arquivos", "*.*")],
            title="Salvar lista de veículos como..."
        )

        if not caminho_arquivo:
            #Usuário cancelou a operação
            return

        try:
            df.to_excel(caminho_arquivo, index=False, engine="openpyxl")
            messagebox.showinfo("Sucesso", f"Dados exportados com sucesso para:\n{caminho_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao exportar os dados: {e}")

    def ver_historico(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um veículo para ver histórico.")
            return

        id_veiculo = self.tree.item(selected_item)["values"][0]
        dados_veiculo = db.buscar_veiculo_por_id(id_veiculo)

        if not dados_veiculo:
            messagebox.showerror("Erro", "Veículo não encontrado no banco de dados.")
            return

        nome_veiculo = f"{dados_veiculo['marca']} {dados_veiculo['modelo']} (Placa: {dados_veiculo['placa']})"


        # Chama uma nova janela para exibir histórico
        HistoricoVeiculoWindow(self, id_veiculo, nome_veiculo)

    def importar_frota(self):
        """Abre um diálogo para selecionar um arquivo CSV e iniciar a importação."""
        caminho_arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo CSV da frota",
            filetypes=[("Arquivos CSV", "*.csv")]
        )

        if not caminho_arquivo:
            return  # Usuário cancelou

        if not messagebox.askyesno("Confirmação",
                                   "Você tem certeza que deseja importar os veículos deste arquivo? Placas duplicadas serão ignoradas."):
            return

        sucessos, falhas, erros = db.importar_veiculos_de_csv(caminho_arquivo)

        mensagem_final = f"Importação Concluída!\n\n- Veículos importados com sucesso: {sucessos}\n- Linhas com erro (ignoradas): {falhas}"

        if erros:
            erros_preview = "\n".join(erros[:5])
            mensagem_final += f"\n\nDetalhes dos primeiros erros:\n{erros_preview}"

        messagebox.showinfo("Resultado da Importação", mensagem_final)
        self.carregar_dados()  # Atualiza a tabela com os novos veículos