import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
import os
import re
from datetime import datetime
from backend import database as db
import pandas as pd


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

        self.campos = ["Marca", "Modelo", "Ano", "Placa", "Cor", "Valor Diária (€)", "Próxima Revisão"]
        self.entradas = {}  # Dicionário para guardar os widgets de entrada

        # --- PASSO 1: Cria todos os campos e popula o dicionário self.entradas ---
        for campo in self.campos:
            frame = ctk.CTkFrame(self)
            frame.pack(padx=20, pady=(10, 0), fill="x")
            label = ctk.CTkLabel(frame, text=campo, width=120, anchor="w")
            label.pack(side="left")
            entry = ctk.CTkEntry(frame)
            entry.pack(side="left", fill="x", expand=True)

            chave_normalizada = campo.lower().replace(" (€)", "").replace(" ", "_")
            self.entradas[chave_normalizada] = entry

            # Preenche os dados se estiver editando
            if dados_veiculo:
                # O nome da coluna no BD pode não ser igual à chave
                chave_bd = chave_normalizada.replace("próxima_revisão", "data_proxima_revisao")
                chave_bd = chave_bd.replace("valor_diária", "valor_diaria")

                valor_bd = dados_veiculo.get(chave_bd)

                if valor_bd is not None:
                    # Formata a data para exibição DD/MM/AAAA
                    if "revisao" in chave_bd:
                        try:
                            valor_bd = datetime.strptime(str(valor_bd), '%Y-%m-%d').strftime('%d/%m/%Y')
                        except ValueError:
                            pass  # Mantém o valor original se o formato for inesperado
                    entry.insert(0, valor_bd)

        # --- PASSO 2: Agora que self.entradas está completo, configura a validação ---
        if 'próxima_revisão' in self.entradas:
            self.data_revisao_entry = self.entradas['próxima_revisão']
            # Cria o comando de validação
            vcmd = (self.register(self.validar_data), '%P')
            # Aplica o comando ao widget
            self.data_revisao_entry.configure(validate="key", validatecommand=vcmd)
            # Define o placeholder se não estiver editando
            if not dados_veiculo:
                self.data_revisao_entry.insert(0, "DD/MM/AAAA")
                # Força uma validação inicial para definir a cor da borda
                self.validar_data("DD/MM/AAAA")

                # --- PASSO 3: Cria o botão de salvar ---
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
        valores = {}
        for chave, entry in self.entradas.items():
            valores[chave] = entry.get()

        if not all(
            v for k, v in valores.items() if k != 'imagem_path'):  # Verifica se todos os campos estão preenchidos
            messagebox.showwarning("Atenção", "Preencha todos os campos!")
            return

        dados_para_db = {}
        try:
            dados_para_db['marca'] = valores['marca']
            dados_para_db['modelo'] = valores['modelo']
            dados_para_db['ano'] = int(valores['ano'])
            dados_para_db['placa'] = valores['placa']
            dados_para_db['cor'] = valores['cor']

            # Remove o "€ " e troca a vírgula por ponto para converter para float
            valor_str = valores['valor_diária'].replace('€', '').strip().replace(',', '.')
            dados_para_db['valor_diaria'] = float(valor_str)

            # Converte data de DD/MM/AAAA para AAAA-MM-DD
            data_revisao_str = valores['próxima_revisão']
            if data_revisao_str == "DD/MM/AAAA":
                messagebox.showerror("Erro de Validação", "Por favor, insira uma data de revisão válida.")
                return
            data_revisao_obj = datetime.strptime(data_revisao_str, '%d/%m/%Y')
            dados_para_db['data_proxima_revisao'] = data_revisao_obj.strftime('%Y-%m-%d')

            # Campo opcional de imagem
            dados_para_db['imagem_path'] = valores.get('imagem_path', None)

        except (ValueError, KeyError) as e:
            logging.error(f"Erro na conversão de dados do formulário: {e}", exc_info=True)
            messagebox.showerror("Erro de Dados",
                                 "Verifique se todos os campos estão preenchidos com valores válidos (números para ano/valor, data correta).")
            return

        # Chama as funções do DB com o dicionário de dados limpo e correto
        if self.dados_veiculo:  # Modo Edição
            db.atualizar_veiculo(self.dados_veiculo['id'], **dados_para_db)
            messagebox.showinfo("Sucesso", "Veículo atualizado com sucesso!")
        else:  # Modo Adição
            if not db.adicionar_veiculo(**dados_para_db):
                messagebox.showerror("Erro", "Não foi possível adicionar o veículo. Verifique se a placa já existe.")
                return
            messagebox.showinfo("Sucesso", "Novo veículo adicionado à frota!")

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
        ctk.CTkButton(button_frame, text="Ver Histórico", command=self.ver_historico_veiculo).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Revisão",
                      command=self.gerir_status_revisao,
                      fg_color="#5e35b1", hover_color="#4527a0").pack(side="right", padx=10)

        self.tree.tag_configure('manutencao', background='#546E7A')  # Cinza Azulado
        self.tree.tag_configure('reservado', background='#1E88E5')  # Azul
        self.tree.tag_configure('alugado', background='#E53935')  # Vermelho
        self.tree.tag_configure('devolucao_hoje', background='#FB8C00')
        self.carregar_dados()

    def carregar_dados(self):
        # 1. Limpa a tabela para evitar duplicatas
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 2. Busca a lista de veículos do backend (já com o status_operacional)
        veiculos = db.listar_veiculos()

        # 3. Itera sobre cada veículo para preparar e inserir os dados
        for v in veiculos:
            # Pega o status calculado pelo backend. Usa '.title()' para capitalizar (ex: 'Disponível')
            status_op = v['status_operacional'].title() if v['status_operacional'] else "Indefinido"

            # Define a tag de cor com base no status operacional
            # As tags devem ser configuradas no __init__ da classe
            tag = ''
            if status_op == 'Manutenção':
                tag = 'manutencao'
            elif status_op == 'Reservado':
                tag = 'reservado'
            elif status_op == 'Alugado':
                tag = 'alugado'  # Assume que você tem uma tag 'alugado'
            elif status_op == 'Devolução Hoje':
                tag = 'devolucao_hoje'

            # Formatação defensiva da data de revisão
            data_revisao_str = ""
            if v['data_proxima_revisao']:
                try:
                    data_revisao_str = datetime.strptime(v['data_proxima_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    data_revisao_str = "Inválida"
            else:
                data_revisao_str = "N/A"

            # Formatação defensiva do valor da diária
            valor_diaria_str = "N/A"
            if v['valor_diaria'] is not None:
                valor_diaria_str = f"€ {v['valor_diaria']:.2f}".replace('.', ',')

            # Formatação defensiva da data de retorno
            data_retorno_str = ""
            if v['data_retorno']:
                try:
                    data_retorno_str = datetime.strptime(v['data_retorno'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    data_retorno_str = "Inválida"

            # Cria a tupla de valores na ordem exata das suas colunas
            # ORDEM: "ID", "Marca", "Modelo", "Placa", "Status", "Revisão", "Valor Diária", "Data Retorno"
            valores_para_inserir = (
                v["id"],
                v["marca"],
                v["modelo"],
                v["placa"],
                status_op,  # Usa o novo status operacional
                data_revisao_str,
                valor_diaria_str,
                data_retorno_str
            )

            # Insere a linha na tabela com os valores e a tag de cor
            self.tree.insert("", "end", values=valores_para_inserir, tags=(tag,))

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
            if db.deletar_veiculo(id_veiculo):
                messagebox.showinfo("Sucesso", "Veículo removido com sucesso.")
                self.carregar_dados()
            else:
                messagebox.showerror("Erro",
                                     "Não foi possível remover o veículo. Verifique se ele possui um histórico de reservas.")

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

    def ver_historico_veiculo(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um veículo para ver o histórico.")
            return

        item_values = self.tree.item(selected_item)["values"]
        id_veiculo = item_values[0]
        nome_veiculo = f"{item_values[1]} {item_values[2]} (Placa: {item_values[3]})"

        # Chama a nova janela para exibir o histórico
        HistoricoVeiculoWindow(self, id_veiculo, nome_veiculo)

    def gerir_status_revisao(self):
        """
        Chama a função do backend para colocar veículos em manutenção e atualiza a view.
        """
        if not messagebox.askyesno("Confirmação",
                                   "Deseja verificar e colocar todos os veículos com revisão vencida ou próxima (15 dias) em status de 'Manutenção'?"):
            return

        num_atualizados = db.colocar_veiculos_revisao_em_manutencao()

        if num_atualizados > 0:
            messagebox.showinfo("Sucesso", f"{num_atualizados} veículo(s) foram atualizados para 'Manutenção'.")
        elif num_atualizados == 0:
            messagebox.showinfo("Informação", "Nenhum veículo necessitava de atualização de status.")
        else:  # num_atualizados == -1
            messagebox.showerror("Erro", "Ocorreu um erro ao atualizar os status. Verifique os logs.")

        self.carregar_dados()


class HistoricoVeiculoWindow(ctk.CTkToplevel):
    def __init__(self, parent, id_veiculo, nome_veiculo):
        super().__init__(parent)
        self.title(f"Histórico de Aluguéis - {nome_veiculo}")
        self.geometry("800x450")
        self.grab_set()

        reservas = db.buscar_reservas_por_veiculo(id_veiculo)

        label = ctk.CTkLabel(self, text=f"Histórico para: {nome_veiculo}", font=("Arial", 16, "bold"))
        label.pack(pady=10)

        if not reservas:
            ctk.CTkLabel(self, text="Este veículo nunca foi alugado.", font=("Arial", 14)).pack(pady=20)
            return

        # Cria uma frame para a tabela para poder adicionar scrollbars
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Configura o Treeview
        style = ttk.Style()
        style.configure("Hist.Treeview", rowheight=25)  # Aumenta a altura da linha
        style.configure("Hist.Treeview.Heading", font=("Arial", 10, "bold"))

        tree = ttk.Treeview(table_frame,
                            columns=("Cliente", "NIF", "Início", "Fim", "Status"),
                            show="headings", style="Hist.Treeview")

        tree.heading("Cliente", text="Cliente")
        tree.heading("NIF", text="NIF Cliente")
        tree.heading("Início", text="Data de Início")
        tree.heading("Fim", text="Data de Fim")
        tree.heading("Status", text="Status da Reserva")

        tree.column("Cliente", width=250)
        tree.column("NIF", width=120, anchor="center")
        tree.column("Início", width=150, anchor="center")
        tree.column("Fim", width=150, anchor="center")
        tree.column("Status", width=120, anchor="center")

        tree.pack(side="left", fill="both", expand=True)

        # Adiciona Scrollbar
        scrollbar = ctk.CTkScrollbar(table_frame, command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        # Popula a tabela
        for r in reservas:
            inicio_f = self.formatar_data_flexivel(r['data_inicio'])
            fim_f = self.formatar_data_flexivel(r['data_fim'])
            tree.insert("", "end", values=(r['nome_completo'], r['nif'], inicio_f, fim_f, r['status'].title()))

    def formatar_data_flexivel(self, data_str):
        """
        Tenta formatar uma string de data, tentando múltiplos formatos.
        Retorna a data formatada ou uma string de erro.
        """
        if not data_str:
            return "N/A"

        # Tenta o formato completo primeiro
        try:
            return datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        except ValueError:
            # Se falhar, tenta o formato de apenas data
            try:
                return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
            except ValueError:
                # Se ambos falharem, retorna um erro claro
                return "Formato Inválido"