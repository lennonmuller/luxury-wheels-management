# 🚗 Luxury Wheels - Sistema de Gestão e Business Intelligence

---

## 📄 Sobre o Projeto

**Luxury Wheels Management** é uma aplicação desktop completa, desenvolvida em Python, para a gestão de uma frota de veículos de luxo. Este projeto vai além de um simples sistema de CRUD, incorporando um **dashboard de Business Intelligence** para transformar dados operacionais em insights acionáveis, e funcionalidades avançadas para otimizar a gestão do negócio.

Este projeto foi construído como parte do meu desenvolvimento contínuo em engenharia de software e análise de dados, com foco em criar uma solução robusta, escalável e orientada a dados, aplicando as melhores práticas do mercado.

---

### ✨ Funcionalidades

O "Luxury Wheels" foi projetado para ir além de um simples sistema de gestão, incorporando inteligência de negócio e robustez de engenharia.

#### Requisitos Essenciais (Base do Projeto)
-   ✅ **Sistema de Autenticação de Usuários:** Login e registo seguros com hashing de senhas.
-   ✅ **CRUD Completo:** Gestão total (Criar, Ler, Atualizar, Apagar) para as entidades de **Veículos**, **Clientes** e **Reservas**.
-   ✅ **Dashboard Central:** Exibição visual de indicadores-chave de performance.
-   ✅ **Exportação de Dados:** Funcionalidade para exportar listas de dados para formatos externos como CSV e Excel.
-   ✅ **Base de Dados Relacional:** Utilização de SQLite com um schema bem definido para garantir a integridade dos dados.

#### Aprimoramentos de Portfólio (Diferencial Nível BMW)

-   🚀 **Inteligência Operacional e Lógica de Negócio Avançada:**
    -   **Cálculo de Status Operacional:** O status de um veículo ('Alugado', 'Disponível', 'Reservado', 'Manutenção') é calculado dinamicamente em tempo real, refletindo a verdadeira situação da frota e não apenas um campo estático.
    -   **Sistema Anti-Colisão de Reservas:** Validação rigorosa que impede a criação de reservas com sobreposição de datas para o mesmo veículo.
    -   **Painel de Controle de Revisões:** O dashboard alerta proativamente sobre revisões futuras e, mais importante, destaca as **vencidas**, permitindo uma gestão proativa da manutenção.
    -   **Gestão de Manutenção com Um Clique:** Funcionalidade que coloca automaticamente todos os veículos que necessitam de revisão em status de 'Manutenção', otimizando o fluxo de trabalho do gestor.

-   📈 **Análise e Visão 360°:**
    -   **Histórico Completo por Cliente:** Permite visualizar todas as reservas passadas e ativas de um cliente específico.
    -   **Análise de Performance por Ativo:** Permite visualizar o histórico de aluguéis de um veículo específico, fornecendo dados para análise de rentabilidade.

-   ⚙️ **Eficiência e Robustez de Engenharia:**
    -   **Importação em Lote (CSV):** Rotinas tolerantes a falhas para importar frotas e clientes, com relatório detalhado de sucessos e erros.
    -   **Fluxo de Trabalho Otimizado:** Atalho contextual para criar uma reserva diretamente a partir da ficha do cliente.
    -   **Sistema de Logging:** Registro de eventos importantes e erros críticos em um arquivo de log com rotação, essencial para diagnóstico e manutenção em produção.
    -   **Testes Unitários:** Suíte de testes com `unittest` para validar a lógica de negócio crítica (ex: segurança de senhas), garantindo a estabilidade e prevenindo regressões.
    -   **Integridade de Dados na Entrada:** Validação em tempo real e padronização de formatos (datas no padrão `DD/MM/AAAA`, moeda `€`) diretamente na interface para prevenir a entrada de dados inválidos.

-   🎨 **UX/UI Polida e Localizada:**
    -   Interface completamente localizada para o mercado europeu/português.
    -   Design de interface profissional com identidade visual (logo), layout em grid e feedback claro ao usuário.

---
### 🛠️ Stack Tecnológico

| Categoria | Tecnologia/Biblioteca | Papel no Projeto |
| :--- | :--- | :--- |
| **Linguagem Principal** | Python 3.12+ | Base para toda a lógica de negócio, análise de dados e interface da aplicação. |
| **Interface Gráfica** | CustomTkinter | Framework para a construção de uma interface de usuário moderna, temática e responsiva. |
| | Pillow (PIL) | Biblioteca para manipulação e exibição de imagens (logo da empresa). |
| **Banco de Dados** | SQLite 3 | Sistema de banco de dados relacional, leve e embarcado, ideal para aplicações desktop. |
| **Análise de Dados** | Pandas | Ferramenta central para manipulação, agregação e análise de dados, servindo como motor para o dashboard e as funcionalidades de exportação/importação. |
| **Visualização de Dados**| Matplotlib & Seaborn | Geração de gráficos estatísticos de alta qualidade (barras, dispersão) integrados diretamente no dashboard da aplicação. |
| **Segurança** | Bcrypt | Algoritmo padrão da indústria para hashing de senhas, garantindo o armazenamento seguro das credenciais dos usuários. |
| **Testes e Qualidade** | Unittest | Framework nativo do Python para a criação e execução de testes unitários, garantindo a estabilidade da lógica de negócio. |
| **Utilitários** | Faker | Geração de dados de simulação realistas (clientes, veículos, reservas) para popular o banco de dados para demonstração e testes. |
| | Openpyxl | Biblioteca para a escrita e leitura de arquivos Excel (.xlsx), utilizada na funcionalidade de exportação. |
| **Versionamento** | Git & GitHub | Sistema de controle de versão para o código-fonte, seguindo práticas como Conventional Commits e Git Tags para releases. |
## 🚀 Como Executar o Projeto

Siga os passos abaixo para executar o projeto em seu ambiente local.

**Pré-requisitos:**
-   [Python 3.11+](https://www.python.org/downloads/)
-   [Git](https://git-scm.com/downloads/)

**1. Clone o Repositório:**
```bash
git clone https://github.com/lennonmuller/luxury-wheels-management.git
cd luxury-wheels-management
```

**2. Crie e Ative um Ambiente Virtual:**
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

**3. Instale as Dependências:**
Com o ambiente virtual ativado, instale todas as bibliotecas necessárias com um único comando:
```bash
pip install -r requirements.txt
```


**4. Criar e Popular o Banco de Dados:**
Para uma experiência de demonstração completa, execute o script de simulação. Ele irá criar e popular o banco de dados com dados realistas.
Execute o seguinte comando no terminal (confirme com 's' quando solicitado):
```bash
python scripts/populate_database.py
```
**5. Executar a Aplicação**
Finalmente, inicie a aplicação:
```bash
python src/main.py
```

**Credenciais de Teste:** 
Você pode criar um usuário através da tela de registro ou adicionar um manualmente. Ex: admin@lw.com, senha 1234.




**📞 Contato:**

Lennon Müler

LinkedIn: www.linkedin.com/in/lennonmuler

Email: lennon-muller@hotmail.com

GitHub: https://github.com/lennonmuller/

