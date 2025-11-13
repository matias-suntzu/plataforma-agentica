"""
Funciones auxiliares para procesamiento de datos
"""

def safe_int_from_insight(value):
    """
    Convierte valores de insights a enteros de forma segura.
    
    Args:
        value: Valor del insight (puede ser None, str, int, float)
    
    Returns:
        int: Valor convertido o 0 si no se puede convertir
    """
    if value is None:
        return 0
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, float):
        return int(value)
    
    if isinstance(value, str):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    return 0


def safe_float_from_insight(value):
    """
    Convierte valores de insights a float de forma segura.
    
    Args:
        value: Valor del insight (puede ser None, str, int, float)
    
    Returns:
        float: Valor convertido o 0.0 si no se puede convertir
    """
    if value is None:
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    return 0.0