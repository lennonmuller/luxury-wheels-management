# src/frontend/dashboard_view.py
from datetime import date, timedelta, datetime
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from backend import analytics as an
from backend import database as db


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # NOVO: Lista para manter referência aos canvases dos gráficos
        self.graficos_canvas = []

        # Configura o estilo dos gráficos para o tema da aplicação
        ctk_theme = ctk.get_appearance_mode()
        if ctk_theme == "Dark":
            plt.style.use('dark_background')
            rc_params = {"axes.facecolor": "#2a2d2e", "figure.facecolor": "#2a2d2e",
                         "grid.color": "#555", "text.color": "white",
                         "xtick.color": "white", "ytick.color": "white",
                         "axes.labelcolor": "white"}
        else:  # Light mode
            plt.style.use('default')
            rc_params = {"text.color": "black", "xtick.color": "black",
                         "ytick.color": "black", "axes.labelcolor": "black"}

        plt.rcParams.update(rc_params)

        # Layout com grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Criar e posicionar os gráficos ---
        self.plotar_faturamento_mensal()
        self.plotar_veiculos_por_status()

        #Chamada de alertas
        self.criar_secao_alertas()

        # Adicione chamadas para outros gráficos aqui

    def plotar_grafico(self, fig, row, col):
        """Função auxiliar para desenhar um gráfico na tela."""
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")


        self.graficos_canvas.append(canvas)
        # É importante fechar a figura do matplotlib para não consumir memória
        plt.close(fig)

    def plotar_faturamento_mensal(self):
        faturamento = an.get_faturamento_mensal()

        fig, ax = plt.subplots(figsize=(6, 4))

        if not faturamento.empty:
            faturamento.index = faturamento.index.astype(str)
            sns.barplot(x=faturamento.index, y=faturamento.values, ax=ax, palette="viridis")
            ax.set_title("Faturamento Mensal (R$)")
            ax.set_ylabel("Valor Total (R$)")
            ax.set_xlabel("Mês/Ano")
            plt.xticks(rotation=45, ha='right')
        else:
            ax.text(0.5, 0.5, "Sem dados de faturamento", ha='center', va='center', fontsize=12)

        fig.tight_layout()
        self.plotar_grafico(fig, 0, 0)

    def plotar_veiculos_por_status(self):
        status_counts = an.get_veiculos_por_status()

        fig, ax = plt.subplots(figsize=(5, 4))

        if not status_counts.empty:
            cores = {"disponível": "#2ecc71", "alugado": "#e74c3c", "manutenção": "#f1c40f"}
            palette_ordenada = [cores.get(status, "#bdc3c7") for status in status_counts.index]

            sns.barplot(x=status_counts.index, y=status_counts.values, ax=ax,
                        hue=status_counts.index, palette=palette_ordenada, legend=False)

            ax.set_title("Distribuição de Veículos por Status")
            ax.set_ylabel("Quantidade")
        else:
            ax.text(0.5, 0.5, "Sem dados de veículos", ha='center', va='center', fontsize=12)

        fig.tight_layout()
        self.plotar_grafico(fig, 0, 1)

    def criar_secao_alertas(self):
        """ Cria e popula a área de alertas de revisão"""
        alertas_frame = ctk.CTkFrame(self)
        alertas_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        label_titulo = ctk.CTkLabel(alertas_frame, text="Alertas - Veículos Próximos da Revisão (15 dias)", font=("Arial", 16, "bold"))
        label_titulo.pack(pady=(10, 5), padx=10, anchor="w")

        veiculos_revisao = db.listar_veiculos_para_revisao()

        if not veiculos_revisao:
            label_sem_alertas = ctk.CTkLabel(alertas_frame, text="Nenhum veículo necessita de revisão em breve.")
            label_sem_alertas.pack(pady=10, padx=10, anchor="w")
            return

        textbox = ctk.CTkTextbox(alertas_frame, height=100)
        textbox.pack(pady=5, padx=10, fill="x", expand=True)

        textbox.tag_config("VENCIDO", foreground="#E57373")
        textbox.tag_config("ALERTA",foreground="#FFD54F")

        hoje = date.today()

        for veiculo in veiculos_revisao:
            data_revisao = datetime.strptime(veiculo['data_proxima_revisao'], '%Y-%m-%d').date()
            data_formatada = data_revisao.strftime("%d/%m/%Y")
            linha_alerta = f"ID: {veiculo['id']} | {veiculo['marca']} {veiculo['modelo']} (Placa: {veiculo['placa']}) - Revisão em: {data_formatada}\n"

            if data_revisao < hoje:
                textbox.insert("end", f"[VENCIDO]{linha_alerta}", "VENCIDO")
            else:
                textbox.insert("end", f"[ALERTA] {linha_alerta}", "ALERTA")

        textbox.configure(state="disabled")  # Bloqueia a edição