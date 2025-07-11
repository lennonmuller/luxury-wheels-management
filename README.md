# 🚗 Luxury Wheels - Sistema de Gestão e Business Intelligence

---

## 📄 Sobre o Projeto

**Luxury Wheels Management** é uma aplicação desktop completa, desenvolvida em Python, para a gestão de uma frota de veículos de luxo. Este projeto vai além de um simples sistema de CRUD, incorporando um **dashboard de Business Intelligence** para transformar dados operacionais em insights acionáveis, e funcionalidades avançadas para otimizar a gestão do negócio.

Este projeto foi construído como parte do meu desenvolvimento contínuo em engenharia de software e análise de dados, com foco em criar uma solução robusta, escalável e orientada a dados, aplicando as melhores práticas do mercado.

---

## ✨ Funcionalidades Principais

*   **Gestão Completa (CRUD):**
    *   Cadastro e gerenciamento de **Veículos** (com status: disponível, alugado, manutenção).
    *   Cadastro e gerenciamento de **Clientes**.
    *   Sistema de **Reservas** transacional, que atualiza o status do veículo automaticamente.
    *   Gestão de **Usuários** do sistema (com login seguro).
*   **Dashboard de Business Intelligence:**
    *   Gráficos visuais para **Faturamento Mensal**.
    *   Análise da **Distribuição de Veículos por Status**.
    *   
*   **Sistema de Alertas Proativo:**
    *   Notificações no dashboard para veículos com **revisão próxima** (próximos 15 dias).
*   **Exportação de Dados:**
    *   Funcionalidade para exportar relatórios (ex: lista de veículos) para **Excel (.xlsx)**.
*   **Segurança:**
    *   Autenticação de usuários com **hashing de senhas** (bcrypt).
    *   Prevenção de **SQL Injection** em todas as interações com o banco de dados.

---

## 🛠️ Arquitetura e Tecnologias Utilizadas

Este projeto foi desenvolvido com uma arquitetura de 3 camadas para garantir a separação de responsabilidades e a manutenibilidade.

*   **Frontend (Apresentação):**
    *   **CustomTkinter:** Para uma interface gráfica moderna, responsiva e com temas.
    *   **Matplotlib & Seaborn:** Para a incorporação de gráficos de alta qualidade no dashboard.
*   **Backend (Lógica de Negócios):**
    *   **Python 3:** Linguagem principal do projeto.
    *   **Pandas:** Para manipulação e análise de dados, servindo como ponte para o dashboard e a exportação.
    *   **Orientação a Objetos (POO)** e princípios **SOLID** (ex: Princípio da Responsabilidade Única) para um código limpo e modular.
*   **Data (Persistência):**
    *   **SQLite:** Banco de dados relacional leve, ideal para aplicações desktop.
    *   **Design de Schema Relacional:** Com uso de chaves primárias e estrangeiras para garantir a integridade dos dados.

---

## 🚀 Como Executar o Projeto

Siga os passos abaixo para executar o projeto em seu ambiente local.

**Pré-requisitos:**
*   Python 3.10 ou superior
*   Git

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
Crie um arquivo requirements.txt com o comando pip freeze > requirements.txt e adicione-o ao seu repositório. As dependências são:
```bash
bcrypt
customtkinter
matplotlib
numpy
openpyxl
pandas
seaborn
```
Em seguida, instale-as:
```bash
pip install -r requirements.txt
```

**4. Execute a Aplicação:**
```bash
python src/main.py
```

_Credenciais de Teste: Você pode criar um usuário através da tela de registro ou adicionar um manualmente. Ex: admin@lw.com, senha 1234.
