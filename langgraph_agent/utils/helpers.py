"""
Funciones Helper Generales
Utilidades comunes para procesamiento de datos
"""

import logging
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


# ========== SAFE EXTRACTORS ==========

def safe_int_from_insight(insight: Dict, field: str, default: int = 0) -> int:
    """
    Extrae un valor entero de un insight de Meta Ads de forma segura.
    
    Args:
        insight: Dict con datos del insight
        field: Nombre del campo a extraer
        default: Valor por defecto si falla
        
    Returns:
        int: Valor extraído o default
        
    Example:
        >>> insight = {'impressions': '12345'}
        >>> safe_int_from_insight(insight, 'impressions')
        12345
    """
    try:
        value = insight.get(field)
        
        if value is None:
            return default
        
        # Si ya es int, retornar
        if isinstance(value, int):
            return value
        
        # Si es string, convertir
        if isinstance(value, str):
            return int(value)
        
        # Si es float, convertir
        if isinstance(value, float):
            return int(value)
        
        return default
    
    except (ValueError, TypeError) as e:
        logger.debug(f"Error convirtiendo {field} a int: {e}")
        return default


def safe_float_from_insight(insight: Dict, field: str, default: float = 0.0) -> float:
    """
    Extrae un valor float de un insight de Meta Ads de forma segura.
    
    Args:
        insight: Dict con datos del insight
        field: Nombre del campo a extraer
        default: Valor por defecto si falla
        
    Returns:
        float: Valor extraído o default
        
    Example:
        >>> insight = {'spend': '123.45'}
        >>> safe_float_from_insight(insight, 'spend')
        123.45
    """
    try:
        value = insight.get(field)
        
        if value is None:
            return default
        
        # Si ya es float, retornar
        if isinstance(value, float):
            return value
        
        # Si es int, convertir
        if isinstance(value, int):
            return float(value)
        
        # Si es string, convertir
        if isinstance(value, str):
            return float(value)
        
        return default
    
    except (ValueError, TypeError) as e:
        logger.debug(f"Error convirtiendo {field} a float: {e}")
        return default


def safe_str_from_insight(insight: Dict, field: str, default: str = "") -> str:
    """
    Extrae un valor string de un insight de forma segura.
    
    Args:
        insight: Dict con datos del insight
        field: Nombre del campo a extraer
        default: Valor por defecto si falla
        
    Returns:
        str: Valor extraído o default
    """
    try:
        value = insight.get(field)
        
        if value is None:
            return default
        
        return str(value)
    
    except Exception as e:
        logger.debug(f"Error convirtiendo {field} a str: {e}")
        return default


# ========== FORMATTERS ==========

def format_currency(value: float, currency: str = "EUR", decimals: int = 2) -> str:
    """
    Formatea un valor monetario.
    
    Args:
        value: Valor numérico
        currency: Código de moneda (EUR, USD, etc.)
        decimals: Número de decimales
        
    Returns:
        str: Valor formateado (ej: "123.45€")
        
    Example:
        >>> format_currency(123.456)
        "123.46€"
    """
    currency_symbols = {
        "EUR": "€",
        "USD": "$",
        "GBP": "£",
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    formatted = f"{value:,.{decimals}f}{symbol}"
    
    return formatted


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formatea un valor como porcentaje.
    
    Args:
        value: Valor numérico (0-100)
        decimals: Número de decimales
        
    Returns:
        str: Valor formateado (ej: "12.34%")
        
    Example:
        >>> format_percentage(12.3456)
        "12.35%"
    """
    return f"{value:.{decimals}f}%"


def format_number(value: int) -> str:
    """
    Formatea un número con separadores de miles.
    
    Args:
        value: Valor numérico
        
    Returns:
        str: Valor formateado (ej: "1,234,567")
        
    Example:
        >>> format_number(1234567)
        "1,234,567"
    """
    return f"{value:,}"


# ========== CALCULATORS ==========

def calculate_ctr(clicks: int, impressions: int) -> float:
    """
    Calcula CTR (Click-Through Rate).
    
    Args:
        clicks: Número de clicks
        impressions: Número de impresiones
        
    Returns:
        float: CTR en porcentaje (0-100)
        
    Example:
        >>> calculate_ctr(50, 1000)
        5.0
    """
    if impressions == 0:
        return 0.0
    
    return (clicks / impressions) * 100


def calculate_cpm(spend: float, impressions: int) -> float:
    """
    Calcula CPM (Cost Per Mille - por cada 1000 impresiones).
    
    Args:
        spend: Gasto total
        impressions: Número de impresiones
        
    Returns:
        float: CPM
        
    Example:
        >>> calculate_cpm(100, 50000)
        2.0
    """
    if impressions == 0:
        return 0.0
    
    return (spend / impressions) * 1000


def calculate_cpc(spend: float, clicks: int) -> float:
    """
    Calcula CPC (Cost Per Click).
    
    Args:
        spend: Gasto total
        clicks: Número de clicks
        
    Returns:
        float: CPC
        
    Example:
        >>> calculate_cpc(100, 50)
        2.0
    """
    if clicks == 0:
        return 0.0
    
    return spend / clicks


def calculate_cpa(spend: float, conversions: int) -> float:
    """
    Calcula CPA (Cost Per Action/Acquisition).
    
    Args:
        spend: Gasto total
        conversions: Número de conversiones
        
    Returns:
        float: CPA
        
    Example:
        >>> calculate_cpa(100, 10)
        10.0
    """
    if conversions == 0:
        return 0.0
    
    return spend / conversions


def calculate_conversion_rate(conversions: int, clicks: int) -> float:
    """
    Calcula ratio de conversión (conversiones / clicks).
    
    Args:
        conversions: Número de conversiones
        clicks: Número de clicks
        
    Returns:
        float: Ratio de conversión en porcentaje (0-100)
        
    Example:
        >>> calculate_conversion_rate(10, 100)
        10.0
    """
    if clicks == 0:
        return 0.0
    
    return (conversions / clicks) * 100


def calculate_roas(revenue: float, spend: float) -> float:
    """
    Calcula ROAS (Return On Ad Spend).
    
    Args:
        revenue: Ingresos generados
        spend: Gasto en publicidad
        
    Returns:
        float: ROAS (ej: 3.0 = 3x retorno)
        
    Example:
        >>> calculate_roas(300, 100)
        3.0
    """
    if spend == 0:
        return 0.0
    
    return revenue / spend


# ========== AGGREGATORS ==========

def aggregate_metrics(items: list, metrics: list = None) -> Dict[str, Any]:
    """
    Agrega métricas de una lista de items.
    
    Args:
        items: Lista de dicts con métricas
        metrics: Lista de métricas a agregar (default: spend, clicks, impressions, conversions)
        
    Returns:
        Dict con métricas agregadas
        
    Example:
        >>> items = [
        ...     {"spend": 100, "clicks": 50},
        ...     {"spend": 150, "clicks": 70}
        ... ]
        >>> aggregate_metrics(items, ["spend", "clicks"])
        {"spend": 250, "clicks": 120, "count": 2}
    """
    if metrics is None:
        metrics = ["spend", "clicks", "impressions", "conversions"]
    
    aggregated = {metric: 0 for metric in metrics}
    aggregated["count"] = len(items)
    
    for item in items:
        for metric in metrics:
            value = item.get(metric, 0)
            
            # Convertir a float si es necesario
            if isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    value = 0
            
            aggregated[metric] += value
    
    return aggregated


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing Helpers...\n")
    
    # Test safe extractors
    print("1. Testing safe extractors...")
    insight = {
        'impressions': '12345',
        'spend': '123.45',
        'name': 'Test Campaign'
    }
    
    assert safe_int_from_insight(insight, 'impressions') == 12345
    assert safe_float_from_insight(insight, 'spend') == 123.45
    assert safe_str_from_insight(insight, 'name') == 'Test Campaign'
    print("   ✅ Safe extractors OK")
    
    # Test formatters
    print("\n2. Testing formatters...")
    assert format_currency(123.456) == "123.46€"
    assert format_percentage(12.3456) == "12.35%"
    assert format_number(1234567) == "1,234,567"
    print("   ✅ Formatters OK")
    
    # Test calculators
    print("\n3. Testing calculators...")
    assert calculate_ctr(50, 1000) == 5.0
    assert calculate_cpm(100, 50000) == 2.0
    assert calculate_cpc(100, 50) == 2.0
    assert calculate_cpa(100, 10) == 10.0
    assert calculate_conversion_rate(10, 100) == 10.0
    assert calculate_roas(300, 100) == 3.0
    print("   ✅ Calculators OK")
    
    # Test aggregators
    print("\n4. Testing aggregators...")
    items = [
        {"spend": 100, "clicks": 50},
        {"spend": 150, "clicks": 70}
    ]
    result = aggregate_metrics(items, ["spend", "clicks"])
    assert result["spend"] == 250
    assert result["clicks"] == 120
    assert result["count"] == 2
    print("   ✅ Aggregators OK")
    
    print("\n✅ Todos los tests pasaron\n")