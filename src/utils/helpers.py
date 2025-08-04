from datetime import datetime
import logging

def parse_datestr_flexible(date_str: str) -> datetime:
    """
    Tenta converter uma string de data em um objeto datetime,
    testando múltiplos formatos comuns.

    Args:
        date_str (str): A string de data a ser convertida.

    Returns:
        datetime: O objeto datetime convertido.

    Raises:
        ValueError: Se a string não corresponder a nenhum dos formatos testados.
    """
    if not isinstance(date_str, str):
        # Se não for uma string (pode ser None ou já um datetime), lida com isso.
        raise TypeError(f"A entrada deve ser uma string, mas foi recebido {type(date_str)}")

    # Formatos a serem testados, do mais específico para o mais geral
    formatos_para_testar = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y',
    ]

    for fmt in formatos_para_testar:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue # Tenta o próximo formato

    # Se nenhum formato funcionar, loga o erro e lança uma exceção
    logging.error(f"Formato de data irreconhecível para a string: '{date_str}'")
    raise ValueError(f"Não foi possível converter a data: {date_str}")