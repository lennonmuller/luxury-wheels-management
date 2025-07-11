import json
import os

# Determina o caminho para o arquivo de configuração na raiz do projeto
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')

def carregar_config():
    """Carrega as configurações do arquivo JSON. Se não existir, cria um vazio."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def salvar_config(config_data):
    """Salva um dicioário de configurações no arquivo JSON."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=4)

def salvar_email_lembrado(email):
    """Salva o email do usuário para ser lembrado."""
    config = carregar_config()
    config['lembrar_email'] = email
    salvar_config(config)

def obter_email_lembrado():
    """Obtém o email salvo, se existir"""
    config = carregar_config()
    return config.get('lembrar_email', '')

def limpar_email_lembrado():
    """Limpa o email salvo das configurações."""
    config = carregar_config()
    if 'lembrar_email' in config:
        del config['lembrar_email']
        salvar_config(config)