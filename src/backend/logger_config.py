import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configura o sistema de logging para a aplicação."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'luxury_wheels.log')

    #Config basica e level INFO de captura de erros:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            #maxBytes: 1MB por arquivo, backupCount: 3 arquivos antigos
            RotatingFileHandler(log_file, maxBytes=1048576, backupCount=3)
        ]
    )

    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("Sistema de Logging Inicializado")
    logger.info("="*50)