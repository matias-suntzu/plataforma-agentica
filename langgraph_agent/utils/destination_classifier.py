"""
Clasificador de Destinos
Responsabilidad: Extraer destino desde el nombre de campaña/adset/anuncio
"""

import re
from typing import Optional


# ========== MAPEO DE DESTINOS ==========

DESTINATION_MAP = {
    # Montaña y Específicas
    "baqueira": "Baqueira",
    "andorra": "Andorra",
    "pirineos": "Pirineos",
    
    # Insulares
    "ibiza": "Ibiza",
    "mallorca": "Mallorca",
    "menorca": "Menorca",
    "canarias": "Canarias",
    
    # Costas
    "cantabria": "Cantabria",
    "costaluz": "Costa de la Luz",
    "costablanca": "Costa Blanca",
    "costasol": "Costa del Sol",
    "costa del sol": "Costa del Sol",  # Variante con espacios
}


# ========== FUNCIONES ==========

def extract_destination(text: str) -> str:
    """
    Extrae el destino desde el nombre de campaña/adset/anuncio.
    Aplica la misma lógica que tu query SQL de BigQuery.
    
    Args:
        text: Nombre de campaña, adset o anuncio
        
    Returns:
        Destino clasificado (ej: "Baqueira", "Costa Blanca", "General")
        
    Examples:
        >>> extract_destination("fbads_es_destino_verano_25.09.25_ibiza_interac")
        "Ibiza"
        
        >>> extract_destination("fbads_es_destino_costablanca_27.08.25_lookalike")
        "Costa Blanca"
        
        >>> extract_destination("fbads_es_destinos_general_2025")
        "General"
    """
    if not text:
        return "General"
    
    text_lower = text.lower()
    
    # Buscar cada destino en el texto
    for keyword, destination in DESTINATION_MAP.items():
        if keyword in text_lower:
            return destination
    
    # Si no encuentra nada, es "General"
    return "General"


def extract_destination_from_adset_name(adset_name: str) -> str:
    """
    Alias de extract_destination() para claridad.
    Específicamente para nombres de adsets.
    """
    return extract_destination(adset_name)


def extract_destination_from_campaign_name(campaign_name: str) -> str:
    """
    Alias de extract_destination() para claridad.
    Específicamente para nombres de campañas.
    """
    return extract_destination(campaign_name)


def extract_destination_from_ad_name(ad_name: str) -> str:
    """
    Alias de extract_destination() para claridad.
    Específicamente para nombres de anuncios.
    """
    return extract_destination(ad_name)


def classify_destinations_in_list(items: list, name_field: str = "name") -> list:
    """
    Clasifica destinos en una lista de elementos (campañas, adsets, anuncios).
    Agrega campo "destination" a cada elemento.
    
    Args:
        items: Lista de dicts con información de campañas/adsets/ads
        name_field: Nombre del campo que contiene el nombre (default: "name")
        
    Returns:
        Lista modificada con campo "destination" agregado
        
    Example:
        >>> items = [
        ...     {"name": "fbads_es_destino_baqueira_27.08.25", "spend": 100},
        ...     {"name": "fbads_es_destino_ibiza_27.08.25", "spend": 200}
        ... ]
        >>> classify_destinations_in_list(items)
        [
            {"name": "...", "spend": 100, "destination": "Baqueira"},
            {"name": "...", "spend": 200, "destination": "Ibiza"}
        ]
    """
    for item in items:
        name = item.get(name_field, "")
        item["destination"] = extract_destination(name)
    
    return items


def aggregate_by_destination(items: list, metrics: list = None) -> dict:
    """
    Agrega métricas por destino.
    
    Args:
        items: Lista de items con campo "destination"
        metrics: Lista de métricas a agregar (default: ["spend", "clicks", "impressions"])
        
    Returns:
        Dict con métricas agregadas por destino
        
    Example:
        >>> items = [
        ...     {"destination": "Baqueira", "spend": 100, "clicks": 50},
        ...     {"destination": "Baqueira", "spend": 150, "clicks": 70},
        ...     {"destination": "Ibiza", "spend": 200, "clicks": 100}
        ... ]
        >>> aggregate_by_destination(items)
        {
            "Baqueira": {"spend": 250, "clicks": 120, "count": 2},
            "Ibiza": {"spend": 200, "clicks": 100, "count": 1}
        }
    """
    if metrics is None:
        metrics = ["spend", "clicks", "impressions", "conversions"]
    
    aggregated = {}
    
    for item in items:
        destination = item.get("destination", "General")
        
        if destination not in aggregated:
            aggregated[destination] = {metric: 0 for metric in metrics}
            aggregated[destination]["count"] = 0
        
        # Agregar métricas
        for metric in metrics:
            value = item.get(metric, 0)
            if isinstance(value, (int, float)):
                aggregated[destination][metric] += value
        
        aggregated[destination]["count"] += 1
    
    return aggregated


def get_top_destinations(items: list, metric: str = "spend", top_n: int = 3) -> list:
    """
    Obtiene los TOP N destinos por una métrica específica.
    
    Args:
        items: Lista de items con campo "destination"
        metric: Métrica para ordenar (default: "spend")
        top_n: Número de destinos a retornar
        
    Returns:
        Lista de destinos ordenados por métrica
        
    Example:
        >>> items = [...]
        >>> get_top_destinations(items, metric="spend", top_n=3)
        ["Baqueira", "Costa Blanca", "Ibiza"]
    """
    aggregated = aggregate_by_destination(items, metrics=[metric])
    
    # Ordenar por métrica
    sorted_destinations = sorted(
        aggregated.items(),
        key=lambda x: x[1].get(metric, 0),
        reverse=True
    )
    
    return [dest for dest, _ in sorted_destinations[:top_n]]


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing Destination Classifier...\n")
    
    test_cases = [
        ("fbads_es_destino_verano_25.09.25_ibiza_interac+interes+sa", "Ibiza"),
        ("fbads_es_destino_costablanca_27.08.25_lookalike_vid3", "Costa Blanca"),
        ("fbads_es_destino_baqueira_27.08.25_interaccion", "Baqueira"),
        ("fbads_es_destino_cantabria_08.10.25_interac", "Cantabria"),
        ("fbads_es_destinos_general_2025", "General"),
    ]
    
    print("📋 TEST: extract_destination()\n")
    
    for name, expected in test_cases:
        result = extract_destination(name)
        status = "✅" if result == expected else "❌"
        print(f"{status} {name[:50]}...")
        print(f"   Expected: {expected}, Got: {result}\n")
    
    # Test agregación
    print("\n📊 TEST: aggregate_by_destination()\n")
    
    items = [
        {"name": "fbads_baqueira_1", "spend": 100, "clicks": 50, "destination": "Baqueira"},
        {"name": "fbads_baqueira_2", "spend": 150, "clicks": 70, "destination": "Baqueira"},
        {"name": "fbads_ibiza_1", "spend": 200, "clicks": 100, "destination": "Ibiza"},
    ]
    
    aggregated = aggregate_by_destination(items)
    print(f"Baqueira: {aggregated['Baqueira']}")
    print(f"Ibiza: {aggregated['Ibiza']}")
    
    # Test TOP destinos
    print("\n🏆 TEST: get_top_destinations()\n")
    
    top_dests = get_top_destinations(items, metric="spend", top_n=2)
    print(f"TOP 2 destinos por gasto: {top_dests}")