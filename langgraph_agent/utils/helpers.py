"""Funciones auxiliares reutilizables"""


def safe_int_from_insight(value):
    """
    Convierte valores de insights de Meta Ads a enteros de forma segura.
    
    Meta Ads puede retornar valores en múltiples formatos:
    - Lista con dict: [{"value": "123"}]
    - Lista con número: [123]
    - Número directo: 123
    - String: "123"
    - None
    
    Args:
        value: Valor retornado por Meta Ads API
        
    Returns:
        int: Valor convertido a entero, 0 si no se puede convertir
    """
    if isinstance(value, list):
        if not value:
            return 0
        
        first = value[0]
        
        # Caso: [{"value": "123"}]
        if isinstance(first, dict) and "value" in first:
            try:
                return int(float(first["value"]))
            except:
                return 0
        
        # Caso: [123] o ["123"]
        if isinstance(first, (int, float, str)):
            try:
                return int(float(first))
            except:
                return 0
        
        return 0
    
    # Caso: None
    if value is None:
        return 0
    
    # Caso: 123 o "123"
    if isinstance(value, (int, float, str)):
        try:
            return int(float(value))
        except:
            return 0
    
    return 0

