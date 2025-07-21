# src/frontend/vehicle_view.py

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
import os
import re
from datetime import datetime
from backend import database as db


# --- CLASSE PARA O FORMULÁRIO DE ADICIONAR/EDITAR (BOA PRÁTICA) ---
class FormularioVeiculo(ctk.CTkToplevel):
    def __init__(self, parent, controller, dados_veiculo=None):
        super().__init__(parent)
        self.controller = controller
        self.parent_view = parent  # Referência à VehicleView para poder atualizá-la
        self.dados_veiculo = dados_veiculo

        self.title("Editar Veículo" if dados_veiculo else "Adicionar Novo Veículo")
        self.geometry("400x550")
        self.resizable(False, False)
        self.grab_set()  # Mantém o foco na janela

        self.campos = ["Marca", "Modelo", "Ano", "Placa", "Cor", "Valor Diária (€)", "Data Proxima Revisao"]
        self.entradas = {}

        for campo in self.campos:
            frame = ctk.CTkFrame(self)
            frame.pack(padx=20, pady=(10, 0), fill="x")
            label = ctk.CTkLabel(frame, text=campo, width=120, anchor="w")
            label.pack(side="left")
            entry = ctk.CTkEntry(frame)
            entry.pack(side="left", fill="x", expand=True)

            chave_coluna = campo.lower().replace(" ", "_")

            if "revisao" in chave_coluna:
                self.data_revisao_entry = entry
                vcmd = (self.register(self.validar_data), '%P')
                entry.configure(validate="key", validatecommand=vcmd)

                if dados_veiculo:
                    data_str = dados_veiculo.get(chave_coluna, '')
                    if data_str:
                        data_obj = datetime.strptime(data_str, '%Y-%m-%d')
                        entry.insert(0, data_obj.strftime('%d/%m/%Y'))
                else:
                    entry.insert(0, "DD/MM/AAAA")
            else:
                if dados_veiculo:
                    entry.insert(0, dados_veiculo.get(chave_coluna, ''))

            self.entradas[chave_coluna] = entry

        texto_botao = "Confirmar Alterações" if dados_veiculo else "Salvar Novo Veículo"
        self.btn_salvar = ctk.CTkButton(self, text=texto_botao, command=self.salvar)
        self.btn_salvar.pack(pady=20)

    def validar_data(self, novo_texto):
        if novo_texto == "":
            self.data_revisao_entry.configure(border_color="gray")
            return True

        if re.match(r"^(|(\d{0,2})(/?(\d{0,2})(/?(\d{0,4}))?)?)$", novo_texto) and len(novo_texto) <= 10:
            if re.match(r"^(0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/\d{4}$", novo_texto):
                self.data_revisao_entry.configure(border_color="green")
            else:
                self.data_revisao_entry.configure(border_color="red")
            return True
        return False

    def salvar(self):
        valores = {chave: entry.get() for chave, entry in self.entradas.items()}

        if not all(valores.values()):
            messagebox.showwarning("Atenção", "Preencha todos os campos!", parent=self)
            return

        # Validação e conversão da data
        try:
            data_revisao_obj = datetime.strptime(valores['data_proxima_revisao'], '%d/%m/%Y')
            valores['data_proxima_revisao'] = data_revisao_obj.strftime('%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Erro de Formato", "A data de revisão está em um formato inválido. Use DD/MM/AAAA.",
                                 parent=self)
            return

        # Validação de tipos numéricos
        try:
            valores['ano'] = int(valores['ano'])
            valores['valor_diaria'] = float(valores['valor_diaria'].replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro de Tipo", "Ano e Valor da Diária devem ser números válidos.", parent=self)
            return

        if self.dados_veiculo:  # Modo Edição
            db.atualizar_veiculo(self.dados_veiculo['id'], **valores)
            messagebox.showinfo("Sucesso", "Veículo atualizado com sucesso!", parent=self)
        else:  # Modo Adição
            if not db.adicionar_veiculo(**valores):
                messagebox.showerror("Erro", "Falha ao adicionar veículo. Verifique se a placa já existe.", parent=self)
                return
            messagebox.showinfo("Sucesso", "Novo veículo adicionado à frota!", parent=self)

        self.parent_view.carregar_dados()
        self.destroy()


# --- CLASSE PRINCIPAL DA VISÃO DE VEÍCULOS ---
class VehicleView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.label = ctk.CTkLabel(self, text="Gestão de Veículos", font=("Arial", 24, "bold"))
        self.label.pack(pady=10, padx=10)

        # Frame para a Tabela e Botões
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Tabela (TreeView)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", borderwidth=0,
                        rowheight=25)
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", font=("Arial", 10, "bold"))
        style.map('Treeview', background=[('selected', '#22559b')])

        # Tags de Cor para Status
        style.configure("Disponivel.Treeview", background="#2a2d2e")
        style.configure("Alugado.Treeview", background="#4a2a2d")  # Cor sutil para alugado
        style.configure("Manutencao.Treeview", background="#4a4a2d")  # Cor sutil para manutenção
        style.configure("Devolucao.Treeview", background="#1f6aa5")  # Cor de destaque para devolução hoje

        self.tree = ttk.Treeview(content_frame,
                                 columns=("ID", "Marca", "Modelo", "Placa", "Status", "Revisão", "Valor Diária", "Data Retorno"),
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
        ctk.CTkButton(button_frame, text="Importar Frota (CSV)", command=self.importar_frota).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Exportar para Excel", command=self.exportar_para_excel).pack(side="right",
                                                                                                       padx=10)

        self.carregar_dados()

    def carregar_dados(self):
        # Limpa a tabela antes de carregar novos dados
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Busca os dados com a query explícita e robusta do backend
        veiculos = db.listar_veiculos()

        for v in veiculos:
            # Prepara cada variável de forma defensiva, tratando valores nulos (None)

            # 1. Status Dinâmico
            status_final = v['status_dinamico'].title() if v['status_dinamico'] else "Indefinido"

            # 2. Data da Próxima Revisão
            data_revisao_str = ""
            if v['data_proxima_revisao'] is not None:
                try:
                    # Converte de 'AAAA-MM-DD' para 'DD/MM/AAAA'
                    data_revisao_str = datetime.strptime(v['data_proxima_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    data_revisao_str = "Data Inválida"
            else:
                data_revisao_str = "Não Definida"

            # 3. Valor da Diária
            valor_diaria_str = ""
            if v['valor_diaria'] is not None:
                # Formata para o padrão Euro com vírgula decimal
                valor_diaria_str = f"€ {v['valor_diaria']:.2f}".replace('.', ',')
            else:
                valor_diaria_str = "N/A"

            # 4. Data de Retorno
            data_retorno_str = ""  # Padrão é vazio para carros não alugados
            if status_final == 'Alugado' and v['data_retorno'] is not None:
                try:
                    # Converte de 'AAAA-MM-DD HH:MM:SS' para 'DD/MM/AAAA'
                    data_retorno_str = datetime.strptime(v['data_retorno'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    data_retorno_str = "Data Inválida"

            # Monta a tupla de valores na ordem exata das colunas da TreeView
            # ORDEM: "ID", "Marca", "Modelo", "Placa", "Status", "Revisão", "Valor Diária", "Data Retorno"
            valores_para_inserir = (
                v["id"],
                v["marca"],
                v["modelo"],
                v["placa"],
                status_final,
                data_revisao_str,
                valor_diaria_str,
                data_retorno_str
            )

            # Insere a linha na tabela
            self.tree.insert("", "end", values=valores_para_inserir)

    def abrir_adicionar(self):
        FormularioVeiculo(self, self.controller)

    def abrir_editar(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um veículo para editar.")
            return

        item_id = self.tree.item(selected_item)["values"][0]
        dados_veiculo_row = db.buscar_veiculo_por_id(item_id)

        if dados_veiculo_row:
            dados_veiculo_dict = dict(dados_veiculo_row)
            FormularioVeiculo(self, self.controller, dados_veiculo_dict)
        else:
            messagebox.showerror("Erro", "Não foi possível encontrar os dados do veículo selecionado.")

    def deletar_veiculo(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um veículo para remover.")
            return

        id_veiculo = self.tree.item(selected_item)["values"][0]

        if messagebox.askyesno("Confirmação", f"Tem certeza que deseja remover o veículo ID {id_veiculo}?"):
            if not db.deletar_veiculo(id_veiculo):
                messagebox.showerror("Erro", "Não é possível remover um veículo com reservas associadas.")
            else:
                messagebox.showinfo("Sucesso", "Veículo removido com sucesso.")
                self.carregar_dados()

    def importar_frota(self):
        caminho_arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo CSV da frota",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        if not caminho_arquivo: return
        if not messagebox.askyesno("Confirmação",
                                   "Deseja importar os veículos deste arquivo? Placas duplicadas serão ignoradas."):
            return
        sucessos, falhas, erros = db.importar_veiculos_de_csv(caminho_arquivo)
        mensagem = f"Importação Concluída!\n\nSucessos: {sucessos}\nFalhas/Duplicados: {falhas}"
        if erros:
            mensagem += f"\n\nExemplo de erros:\n" + "\n".join(erros[:3])
        messagebox.showinfo("Resultado da Importação", mensagem)
        self.carregar_dados()

    def exportar_para_excel(self):
        veiculos = db.listar_veiculos()
        if not veiculos:
            messagebox.showinfo("Informação", "Não há veículos para exportar.")
            return

        dados_veiculos = [dict(v) for v in veiculos]
        df = pd.DataFrame(dados_veiculos)
        df.rename(columns={'valor_diaria': 'valor_diaria_eur'}, inplace=True)

        caminho_arquivo = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Arquivos Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
            title="Salvar lista de veículos"
        )
        if not caminho_arquivo: return

        try:
            df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
            messagebox.showinfo("Sucesso", f"Dados exportados com sucesso para:\n{caminho_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao exportar os dados: {e}")