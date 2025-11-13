"""
Herramientas del agente (funciones locales)
Importa y exporta todas las funciones de herramientas
"""

# Campañas
from .campaigns import (
    listar_campanas_func,
    buscar_id_campana_func
)

# Anuncios
from .ads import (
    obtener_anuncios_por_rendimiento_func
)

# Métricas
from .metrics import (
    get_all_campaigns_metrics_func
)

# Recomendaciones
from .recommendations import (
    get_campaign_recommendations_func,
    get_campaign_details_func
)

# Acciones
from .actions import (
    update_adset_budget_func
)

# Integraciones (opcionales)
try:
    from .integrations import (
        enviar_alerta_slack_func,
        generar_reporte_slides_func
    )
except ImportError:
    # Si no existen, definir funciones dummy
    def enviar_alerta_slack_func(*args, **kwargs):
        raise NotImplementedError("Integración Slack no disponible")
    
    def generar_reporte_slides_func(*args, **kwargs):
        raise NotImplementedError("Integración Google Slides no disponible")


__all__ = [
    # Campañas
    'listar_campanas_func',
    'buscar_id_campana_func',
    
    # Anuncios
    'obtener_anuncios_por_rendimiento_func',
    
    # Métricas
    'get_all_campaigns_metrics_func',
    
    # Recomendaciones
    'get_campaign_recommendations_func',
    'get_campaign_details_func',
    
    # Acciones
    'update_adset_budget_func',
    
    # Integraciones
    'enviar_alerta_slack_func',
    'generar_reporte_slides_func',
]