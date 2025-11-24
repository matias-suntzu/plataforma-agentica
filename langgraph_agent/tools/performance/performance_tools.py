"""
Herramientas de Rendimiento de Campañas
Responsabilidad: Métricas, gasto, conversiones, comparaciones
"""

import json
import logging
from datetime import datetime, timedelta
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.adobjects.ad import Ad

from ...models.schemas import BaseModel, Field
from ...utils.meta_api import get_account
from ...utils.helpers import safe_int_from_insight
from ...config.settings import settings


from ...utils.destination_classifier import (
      extract_destination,
      classify_destinations_in_list,
      aggregate_by_destination,
      get_top_destinations
  )

from typing import List, Dict

logger = logging.getLogger(__name__)

# ========== CONFIGURACIÓN DE TIPOS DE CONVERSIÓN ==========

# 🆕 Mapeo de action_type de Meta API a tipos de conversión del funnel
CONVERSION_TYPE_MAPPING = {
    # Subscriber (interés inicial)
    "subscribe": "subscriber",
    "lead": "subscriber",  # Leads genéricos se consideran subscribers
    "complete_registration": "subscriber",
    
    # MQL (Marketing Qualified Lead)
    "marketing_qualified_lead": "mql",
    "mql": "mql",
    
    # SQL (Sales Qualified Lead)
    "sales_qualified_lead": "sql",
    "sql": "sql",
    
    # Customer (conversión final)
    "purchase": "customer",
    "add_payment_info": "customer",
    "initiate_checkout": "customer",
    
    # Otros eventos de conversión
    "add_to_cart": "engagement",
    "view_content": "engagement",
}

# 🆕 Eventos de conversión de interés (para filtrar)
CONVERSION_EVENTS = [
    'subscribe', 'lead', 'complete_registration',
    'marketing_qualified_lead', 'mql',
    'sales_qualified_lead', 'sql',
    'purchase', 'add_payment_info', 'initiate_checkout'
]


# ========== SCHEMAS ==========

class ObtenerMetricasCampanaInput(BaseModel):
    """Obtiene métricas de rendimiento de una campaña"""
    campana_id: str = Field(description="ID de la campaña")
    date_preset: str = Field(default="last_7d", description="Período: last_7d, last_month, etc.")
    date_start: str = Field(default=None, description="Fecha inicio personalizada (YYYY-MM-DD)")
    date_end: str = Field(default=None, description="Fecha fin personalizada (YYYY-MM-DD)")


class ObtenerMetricasCampanaOutput(BaseModel):
    """Salida con métricas completas"""
    datos_json: str


class ObtenerAnunciosPorRendimientoInput(BaseModel):
    """Obtiene TOP N anuncios de una campaña ordenados por métrica específica"""
    campana_id: str = Field(description="ID de la campaña")
    date_preset: str = Field(default="last_7d", description="Período")
    date_start: str = Field(default=None, description="Fecha inicio")
    date_end: str = Field(default=None, description="Fecha fin")
    limite: int = Field(default=3, description="TOP N anuncios")
    ordenar_por: str = Field(
        default="clicks", 
        description="Métrica: clicks, ctr, cpa, conversiones, impressions, cpc, spend, subscriber, mql, sql"
    )


class ObtenerAnunciosPorRendimientoOutput(BaseModel):
    """Salida con TOP anuncios"""
    datos_json: str


class CompararPeriodosInput(BaseModel):
    """🆕 Compara métricas entre 2 períodos"""
    campana_id: str = Field(description="ID de la campaña (None = todas)")
    periodo_1: str = Field(description="Período 1: 'last_7d', 'this_week', 'custom'")
    periodo_2: str = Field(description="Período 2: 'previous_7d', 'last_week', 'custom'")
    fecha_inicio_1: str = Field(default=None, description="Si periodo_1='custom': YYYY-MM-DD")
    fecha_fin_1: str = Field(default=None, description="Si periodo_1='custom': YYYY-MM-DD")
    fecha_inicio_2: str = Field(default=None, description="Si periodo_2='custom': YYYY-MM-DD")
    fecha_fin_2: str = Field(default=None, description="Si periodo_2='custom': YYYY-MM-DD")


class CompararPeriodosOutput(BaseModel):
    """Salida con comparación de períodos"""
    datos_json: str


class ObtenerMetricasGlobalesInput(BaseModel):
    """Obtiene métricas de TODAS las campañas"""
    date_preset: str = Field(default="last_7d", description="Período")


class ObtenerMetricasGlobalesOutput(BaseModel):
    """Salida con métricas globales"""
    datos_json: str


class ObtenerMetricasPorDestinoInput(BaseModel):
    """Obtiene métricas agregadas por destino"""
    date_preset: str = Field(default="last_7d", description="Período")
    date_start: str = Field(default=None, description="Fecha inicio (YYYY-MM-DD)")
    date_end: str = Field(default=None, description="Fecha fin (YYYY-MM-DD)")
    destino: str = Field(default=None, description="Filtrar por destino específico")


class ObtenerMetricasPorDestinoOutput(BaseModel):
    """Salida con métricas por destino"""
    datos_json: str


class ObtenerCPAGlobalInput(BaseModel):
    """Obtiene CPA global de todas las campañas"""
    date_preset: str = Field(default="last_7d", description="Período")


class ObtenerCPAGlobalOutput(BaseModel):
    """Salida con CPA global"""
    datos_json: str


class ObtenerMetricasAdsetInput(BaseModel):
    """Obtiene métricas a nivel de adset"""
    campana_id: str = Field(description="ID de la campaña")
    date_preset: str = Field(default="last_7d", description="Período")


class ObtenerMetricasAdsetOutput(BaseModel):
    """Salida con métricas de adsets"""
    datos_json: str


class CompararDestinosInput(BaseModel):
    """Compara rendimiento entre destinos"""
    destinos: List[str] = Field(description="Lista de destinos a comparar")
    date_preset: str = Field(default="last_7d", description="Período")


class CompararDestinosOutput(BaseModel):
    """Salida con comparación de destinos"""
    datos_json: str

class ObtenerMetricasCampanaInput(BaseModel):
    """Obtiene métricas de rendimiento de una campaña"""
    campana_id: str = Field(description="ID de la campaña")
    date_preset: str = Field(default="last_7d", description="Período: last_7d, last_month, etc.")
    date_start: str = Field(default=None, description="Fecha inicio personalizada (YYYY-MM-DD)")
    date_end: str = Field(default=None, description="Fecha fin personalizada (YYYY-MM-DD)")
    incluir_funnel: bool = Field(default=True, description="🆕 Incluir métricas del funnel (Subscriber/MQL/SQL)")



class ObtenerMetricasCampanaOutput(BaseModel):
    """Salida con métricas completas"""
    datos_json: str

class CompararAnunciosInput(BaseModel):
    """Compara rendimiento de anuncios de una campaña"""
    campana_id: str = Field(description="ID de la campaña")
    periodo_actual: str = Field(default="last_7d", description="Período actual")
    periodo_anterior: str = Field(default="previous_7d", description="Período anterior")
    metrica_ordenar: str = Field(default="cpa", description="Métrica para ordenar: cpa, cpc, ctr, conversiones")


class CompararAnunciosOutput(BaseModel):
    """Salida con comparación de anuncios"""
    datos_json: str

class CompararAnunciosGlobalesInput(BaseModel):
    """Compara anuncios de TODAS las campañas activas"""
    periodo_actual: str = Field(default="last_7d", description="Período actual")
    periodo_anterior: str = Field(default="previous_7d", description="Período anterior")
    limite_campanas: int = Field(default=10, description="Máximo de campañas a analizar")


class CompararAnunciosGlobalesOutput(BaseModel):
    """Salida con comparación global de anuncios"""
    datos_json: str

# 🆕 NUEVO SCHEMA: Análisis del Funnel de Conversiones
class ObtenerFunnelConversionesInput(BaseModel):
    """Analiza el funnel completo de conversiones (Subscriber → MQL → SQL → Customer)"""
    campana_id: str = Field(default=None, description="ID de la campaña (None = todas)")
    date_preset: str = Field(default="last_7d", description="Período")
    date_start: str = Field(default=None, description="Fecha inicio")
    date_end: str = Field(default=None, description="Fecha fin")


class ObtenerFunnelConversionesOutput(BaseModel):
    """Salida con análisis del funnel"""
    datos_json: str

# ========== MAPEO DE DATE PRESETS ==========

DATE_PRESET_MAP = {
    "ultima semana": "last_7d",
    "última semana": "last_7d",
    "semana pasada": "last_7d",
    "ultimos 7 dias": "last_7d",
    "últimos 7 días": "last_7d",
    "last_week": "last_7d",
    
    "ultimos 14 dias": "last_14d",
    "últimos 14 días": "last_14d",
    
    "ultimo mes": "last_28d",
    "último mes": "last_28d",
    "ultimos 28 dias": "last_28d",
    "últimos 28 días": "last_28d",
    
    "este mes": "this_month",
    "mes actual": "this_month",
    
    "mes pasado": "last_month",
    
    "hoy": "today",
    "ayer": "yesterday",
}


def normalize_date_preset(date_preset: str) -> str:
    """Normaliza un date_preset a un valor válido de Meta API"""
    valid_presets = [
        "today", "yesterday", "this_month", "last_month",
        "this_quarter", "last_3d", "last_7d", "last_14d",
        "last_28d", "last_30d", "last_90d", "last_week_mon_sun",
        "last_week_sun_sat", "last_quarter", "last_year",
        "this_week_mon_today", "this_week_sun_today",
        "this_year", "maximum"
    ]
    
    if date_preset in valid_presets:
        return date_preset
    
    normalized = DATE_PRESET_MAP.get(date_preset.lower())
    
    if normalized:
        logger.info(f"📅 Normalizando date_preset: '{date_preset}' → '{normalized}'")
        return normalized
    
    logger.warning(f"⚠️ date_preset inválido: '{date_preset}'. Usando 'last_7d'")
    return "last_7d"

def categorize_conversion(action_type: str) -> str:
    """
    Categoriza un action_type en su tipo de conversión del funnel.
    
    Args:
        action_type: Tipo de acción de Meta API (ej: 'subscribe', 'mql', 'purchase')
        
    Returns:
        Categoría: 'subscriber', 'mql', 'sql', 'customer', 'engagement', 'other'
    """
    # Buscar en mapeo
    for key, category in CONVERSION_TYPE_MAPPING.items():
        if key in action_type.lower():
            return category
    
    # Por defecto, categorizar según palabras clave
    action_lower = action_type.lower()
    
    if any(kw in action_lower for kw in ['subscribe', 'lead', 'registration']):
        return 'subscriber'
    elif 'mql' in action_lower or 'marketing' in action_lower:
        return 'mql'
    elif 'sql' in action_lower or 'sales' in action_lower:
        return 'sql'
    elif any(kw in action_lower for kw in ['purchase', 'payment', 'checkout']):
        return 'customer'
    else:
        return 'other'


def extract_conversion_metrics(insight: dict) -> Dict[str, int]:
    """
    Extrae métricas de conversión organizadas por tipo (Subscriber/MQL/SQL/Customer).
    
    Args:
        insight: Insight de Meta API con campo 'actions'
        
    Returns:
        Dict con conversiones por tipo y detalle
        {
            "subscriber": 15,
            "mql": 8,
            "sql": 3,
            "customer": 2,
            "total": 28,
            "detail": {"subscribe": 10, "lead": 5, ...}
        }
    """
    conversions = {
        "subscriber": 0,
        "mql": 0,
        "sql": 0,
        "customer": 0,
        "engagement": 0,
        "other": 0,
        "total": 0,
        "detail": {}
    }
    
    actions = insight.get('actions', [])
    
    for action in actions:
        action_type = action.get('action_type', '')
        value = int(action.get('value', 0))
        
        # Guardar detalle
        conversions["detail"][action_type] = value
        
        # Categorizar
        category = categorize_conversion(action_type)
        conversions[category] += value
        conversions["total"] += value
    
    return conversions


def calculate_conversion_rate(conversions_from: int, conversions_to: int) -> float:
    """
    Calcula ratio de conversión entre dos etapas del funnel.
    
    Args:
        conversions_from: Conversiones en etapa origen
        conversions_to: Conversiones en etapa destino
        
    Returns:
        Porcentaje de conversión (0-100)
    """
    if conversions_from == 0:
        return 0.0
    return round((conversions_to / conversions_from) * 100, 2)

# ========== FUNCIONES ==========

def obtener_metricas_campana_func(input: ObtenerMetricasCampanaInput) -> ObtenerMetricasCampanaOutput:
    """
    🆕 ACTUALIZADO: Obtiene métricas de rendimiento de UNA campaña específica.
    
    Ahora incluye:
    - Métricas tradicionales (gasto, clicks, CTR, etc.)
    - 🆕 Conversiones por tipo (Subscriber, MQL, SQL, Customer)
    - 🆕 Ratios de conversión entre etapas del funnel
    - 🆕 CPA por tipo de conversión
    """
    try:
        campaign = Campaign(input.campana_id)
        
        from ..tools.performance.performance_tools import normalize_date_preset
        date_preset_normalized = normalize_date_preset(input.date_preset)

        use_custom = bool(input.date_start and input.date_end)
        params = {'level': 'campaign'}
        
        if use_custom:
            params['time_range'] = {'since': input.date_start, 'until': input.date_end}
            periodo_str = f"{input.date_start} a {input.date_end}"
        else:
            params['date_preset'] = date_preset_normalized
            periodo_str = date_preset_normalized
        
        fields = [
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.ctr,
            AdsInsights.Field.cpm,
            AdsInsights.Field.cpc,
            AdsInsights.Field.actions,
            AdsInsights.Field.conversions,
            AdsInsights.Field.conversion_values,
        ]
        
        insights = campaign.get_insights(fields=fields, params=params)
        
        if not insights:
            return ObtenerMetricasCampanaOutput(
                datos_json=json.dumps({
                    "error": f"No hay datos para campaña {input.campana_id} en {periodo_str}"
                })
            )
        
        # Agregar métricas tradicionales
        total_spend = 0.0
        total_impressions = 0
        total_clicks = 0
        valor_conversion_total = 0.0
        
        # 🆕 Nuevas métricas del funnel
        funnel_conversions = {
            "subscriber": 0,
            "mql": 0,
            "sql": 0,
            "customer": 0,
            "engagement": 0,
            "other": 0,
            "total": 0,
            "detail": {}
        }
        
        for insight in insights:
            total_spend += float(insight.get('spend', 0))
            total_impressions += int(insight.get('impressions', 0))
            total_clicks += int(insight.get('clicks', 0))
            
            # 🆕 Extraer conversiones por tipo
            conversions_by_type = extract_conversion_metrics(insight)
            
            for key in ["subscriber", "mql", "sql", "customer", "engagement", "other", "total"]:
                funnel_conversions[key] += conversions_by_type[key]
            
            for action_type, value in conversions_by_type["detail"].items():
                funnel_conversions["detail"][action_type] = funnel_conversions["detail"].get(action_type, 0) + value
            
            # Valor de conversiones
            for cv in insight.get('conversion_values', []):
                valor_conversion_total += float(cv.get('value', 0))
        
        # Calcular métricas derivadas
        total_conversiones = funnel_conversions["total"]
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
        cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        cpa = (total_spend / total_conversiones) if total_conversiones > 0 else 0
        ratio_conversion = (total_conversiones / total_clicks * 100) if total_clicks > 0 else 0
        
        # 🆕 Calcular CPA por tipo de conversión
        cpa_por_tipo = {}
        for conv_type in ["subscriber", "mql", "sql", "customer"]:
            count = funnel_conversions[conv_type]
            cpa_por_tipo[conv_type] = round(total_spend / count, 2) if count > 0 else None
        
        # 🆕 Calcular ratios de conversión del funnel
        funnel_ratios = {
            "subscriber_to_mql": calculate_conversion_rate(
                funnel_conversions["subscriber"], 
                funnel_conversions["mql"]
            ),
            "mql_to_sql": calculate_conversion_rate(
                funnel_conversions["mql"], 
                funnel_conversions["sql"]
            ),
            "sql_to_customer": calculate_conversion_rate(
                funnel_conversions["sql"], 
                funnel_conversions["customer"]
            ),
            "subscriber_to_customer": calculate_conversion_rate(
                funnel_conversions["subscriber"], 
                funnel_conversions["customer"]
            )
        }
        
        output = {
            "campaign_id": input.campana_id,
            "periodo": periodo_str,
            "metricas_basicas": {
                "gasto_total_eur": round(total_spend, 2),
                "impresiones": total_impressions,
                "clicks": total_clicks,
                "ctr_porcentaje": round(ctr, 2),
                "cpm_eur": round(cpm, 2),
                "cpc_eur": round(cpc, 2),
            },
            # 🆕 Métricas del funnel de conversiones
            "conversiones_funnel": {
                "subscriber": funnel_conversions["subscriber"],
                "mql": funnel_conversions["mql"],
                "sql": funnel_conversions["sql"],
                "customer": funnel_conversions["customer"],
                "total": total_conversiones,
            },
            "cpa_por_tipo": cpa_por_tipo,
            "ratios_funnel": funnel_ratios,
            "metricas_avanzadas": {
                "cpa_global_eur": round(cpa, 2),
                "ratio_conversion_porcentaje": round(ratio_conversion, 2),
                "valor_conversion_total_eur": round(valor_conversion_total, 2),
            },
            # Detalle completo de conversiones (para debugging)
            "conversiones_detalle": funnel_conversions["detail"] if input.incluir_funnel else None
        }
        
        logger.info(
            f"✅ Métricas de campaña {input.campana_id}: "
            f"{total_spend}€, {total_conversiones} conversiones "
            f"(Subs: {funnel_conversions['subscriber']}, MQL: {funnel_conversions['mql']}, "
            f"SQL: {funnel_conversions['sql']}, Customers: {funnel_conversions['customer']})"
        )
        
        return ObtenerMetricasCampanaOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas: {e}")
        return ObtenerMetricasCampanaOutput(datos_json=json.dumps({"error": str(e)}))


def obtener_anuncios_por_rendimiento_func(input: ObtenerAnunciosPorRendimientoInput) -> "ObtenerAnunciosPorRendimientoOutput":
    """
    🆕 ACTUALIZADO: Obtiene TOP N anuncios ordenados por métrica FLEXIBLE.
    
    Ahora soporta ordenar por:
    - Métricas tradicionales: clicks, ctr, cpa, conversiones, impressions, cpc, spend
    - 🆕 Tipos de conversión: subscriber, mql, sql, customer
    """
    try:
        campaign = Campaign(input.campana_id)
        
        from ..tools.performance.performance_tools import normalize_date_preset
        date_preset_normalized = normalize_date_preset(input.date_preset)

        use_custom = bool(input.date_start and input.date_end)
        params = {'level': 'ad'}
        
        if use_custom:
            params['time_range'] = {'since': input.date_start, 'until': input.date_end}
        else:
            params['date_preset'] = date_preset_normalized
        
        fields = [
            AdsInsights.Field.ad_id,
            AdsInsights.Field.ad_name,
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.ctr,
            AdsInsights.Field.cpm,
            AdsInsights.Field.cpc,
            AdsInsights.Field.actions,
        ]
        
        insights = campaign.get_insights(fields=fields, params=params)
        
        if not insights:
            return ObtenerAnunciosPorRendimientoOutput(
                datos_json=json.dumps({
                    "error": f"No hay datos de anuncios para campaña {input.campana_id}"
                })
            )
        
        anuncios = []
        for insight in insights:
            # 🆕 Extraer conversiones por tipo
            conversions_by_type = extract_conversion_metrics(insight)
            
            spend = float(insight.get('spend', 0))
            clicks = int(insight.get('clicks', 0))
            impressions = int(insight.get('impressions', 0))
            ctr = float(insight.get('ctr', 0))
            cpc = float(insight.get('cpc', 0))
            
            # Calcular CPAs por tipo
            cpa_subscriber = (spend / conversions_by_type["subscriber"]) if conversions_by_type["subscriber"] > 0 else float('inf')
            cpa_mql = (spend / conversions_by_type["mql"]) if conversions_by_type["mql"] > 0 else float('inf')
            cpa_sql = (spend / conversions_by_type["sql"]) if conversions_by_type["sql"] > 0 else float('inf')
            cpa_customer = (spend / conversions_by_type["customer"]) if conversions_by_type["customer"] > 0 else float('inf')
            cpa_total = (spend / conversions_by_type["total"]) if conversions_by_type["total"] > 0 else float('inf')
            
            anuncios.append({
                "ad_id": insight.get('ad_id'),
                "ad_name": insight.get('ad_name', 'Sin nombre'),
                "spend_eur": round(spend, 2),
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(ctr, 2),
                "cpm": round(float(insight.get('cpm', 0)), 2),
                "cpc": round(cpc, 2),
                # 🆕 Conversiones por tipo
                "conversiones_subscriber": conversions_by_type["subscriber"],
                "conversiones_mql": conversions_by_type["mql"],
                "conversiones_sql": conversions_by_type["sql"],
                "conversiones_customer": conversions_by_type["customer"],
                "conversiones_total": conversions_by_type["total"],
                # 🆕 CPAs por tipo
                "cpa_subscriber": round(cpa_subscriber, 2) if cpa_subscriber != float('inf') else None,
                "cpa_mql": round(cpa_mql, 2) if cpa_mql != float('inf') else None,
                "cpa_sql": round(cpa_sql, 2) if cpa_sql != float('inf') else None,
                "cpa_customer": round(cpa_customer, 2) if cpa_customer != float('inf') else None,
                "cpa_total": round(cpa_total, 2) if cpa_total != float('inf') else None,
            })
        
        # 🔥 LÓGICA DE ORDENAMIENTO FLEXIBLE (actualizada con nuevos tipos)
        metrica_key_map = {
            "clicks": ("clicks", True),
            "ctr": ("ctr", True),
            "conversiones": ("conversiones_total", True),
            "impressions": ("impressions", True),
            "spend": ("spend_eur", False),
            "cpa": ("cpa_total", False),
            "cpc": ("cpc", False),
            # 🆕 Nuevos ordenamientos por tipo de conversión
            "subscriber": ("conversiones_subscriber", True),
            "mql": ("conversiones_mql", True),
            "sql": ("conversiones_sql", True),
            "customer": ("conversiones_customer", True),
        }
        
        sort_key, reverse_order = metrica_key_map.get(
            input.ordenar_por.lower(), 
            ("clicks", True)
        )
        
        def safe_sort_key(x):
            val = x.get(sort_key)
            if val is None or val == float('inf'):
                return float('-inf') if reverse_order else float('inf')
            return val
        
        top_anuncios = sorted(anuncios, key=safe_sort_key, reverse=reverse_order)[:input.limite]
        
        output = {
            "campaign_id": input.campana_id,
            "top_n": len(top_anuncios),
            "ordenado_por": input.ordenar_por,
            "anuncios": top_anuncios
        }
        
        logger.info(f"✅ TOP {len(top_anuncios)} anuncios de campaña {input.campana_id} (ordenado por {input.ordenar_por})")
        return "ObtenerAnunciosPorRendimientoOutput"(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo anuncios: {e}")
        return "ObtenerAnunciosPorRendimientoOutput"(datos_json=json.dumps({"error": str(e)}))


def comparar_periodos_func(input: CompararPeriodosInput) -> CompararPeriodosOutput:
    """
    🆕 Compara métricas entre 2 períodos.
    
    Ejemplo: "última semana vs resto del mes"
    
    Returns:
        Métricas de ambos períodos + deltas calculados
    """
    try:
        # Función auxiliar para obtener métricas de un período
        def obtener_metricas_periodo(campana_id, periodo, fecha_inicio, fecha_fin):
            params = {'level': 'campaign'}
            
            periodo_normalized = normalize_date_preset(periodo) if periodo != 'custom' else 'custom'

            if periodo == 'custom' and fecha_inicio and fecha_fin:
                params['time_range'] = {'since': fecha_inicio, 'until': fecha_fin}
            elif periodo_normalized == 'custom':
                # Si el usuario dijo "this_week" o similar, calcular fechas
                hoy = datetime.now()
                if periodo in ['this_week', 'esta semana']:
                    lunes = hoy - timedelta(days=hoy.weekday())
                    params['time_range'] = {
                        'since': lunes.strftime('%Y-%m-%d'),
                        'until': hoy.strftime('%Y-%m-%d')
                    }
                else:
                    params['date_preset'] = periodo_normalized
            else:
                params['date_preset'] = periodo_normalized
            
            fields = [
                AdsInsights.Field.spend,
                AdsInsights.Field.impressions,
                AdsInsights.Field.clicks,
                AdsInsights.Field.ctr,
                AdsInsights.Field.cpm,
                AdsInsights.Field.cpc,
                AdsInsights.Field.actions,
            ]
            
            if campana_id != "None":
                campaign = Campaign(campana_id)
                insights = campaign.get_insights(fields=fields, params=params)
            else:
                # Todas las campañas
                account = get_account()
                insights = account.get_insights(fields=fields, params=params)
            
            # Agregar métricas
            total_spend = 0.0
            total_impressions = 0
            total_clicks = 0
            total_conversiones = 0
            
            for insight in insights:
                total_spend += float(insight.get('spend', 0))
                total_impressions += int(insight.get('impressions', 0))
                total_clicks += int(insight.get('clicks', 0))
                
                for action in insight.get('actions', []):
                    if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                        total_conversiones += int(action.get('value', 0))
            
            ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
            cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
            cpa = (total_spend / total_conversiones) if total_conversiones > 0 else 0
            
            return {
                "spend": round(total_spend, 2),
                "impressions": total_impressions,
                "clicks": total_clicks,
                "ctr": round(ctr, 2),
                "cpm": round(cpm, 2),
                "cpc": round(cpc, 2),
                "conversiones": total_conversiones,
                "cpa": round(cpa, 2)
            }
        
        # Obtener métricas de ambos períodos
        metricas_1 = obtener_metricas_periodo(
            input.campana_id,
            input.periodo_1,
            input.fecha_inicio_1,
            input.fecha_fin_1
        )
        
        metricas_2 = obtener_metricas_periodo(
            input.campana_id,
            input.periodo_2,
            input.fecha_inicio_2,
            input.fecha_fin_2
        )
        
        # Calcular deltas
        def calcular_delta(val1, val2):
            if val2 == 0:
                return {"absoluto": val1, "porcentaje": 0}
            delta_abs = val1 - val2
            delta_pct = (delta_abs / val2) * 100
            return {
                "absoluto": round(delta_abs, 2),
                "porcentaje": round(delta_pct, 2)
            }
        
        deltas = {
            "spend": calcular_delta(metricas_1['spend'], metricas_2['spend']),
            "impressions": calcular_delta(metricas_1['impressions'], metricas_2['impressions']),
            "clicks": calcular_delta(metricas_1['clicks'], metricas_2['clicks']),
            "ctr": calcular_delta(metricas_1['ctr'], metricas_2['ctr']),
            "cpm": calcular_delta(metricas_1['cpm'], metricas_2['cpm']),
            "cpc": calcular_delta(metricas_1['cpc'], metricas_2['cpc']),
            "conversiones": calcular_delta(metricas_1['conversiones'], metricas_2['conversiones']),
            "cpa": calcular_delta(metricas_1['cpa'], metricas_2['cpa']),
        }
        
        # Generar análisis cualitativo
        analisis = []
        if deltas['conversiones']['porcentaje'] > 10:
            analisis.append(f"✅ Mejora significativa en conversiones (+{deltas['conversiones']['porcentaje']}%)")
        elif deltas['conversiones']['porcentaje'] < -10:
            analisis.append(f"⚠️ Caída en conversiones ({deltas['conversiones']['porcentaje']}%)")
        
        if deltas['cpa']['porcentaje'] < -5:
            analisis.append(f"✅ CPA más eficiente ({deltas['cpa']['porcentaje']}%)")
        elif deltas['cpa']['porcentaje'] > 5:
            analisis.append(f"⚠️ CPA más alto (+{deltas['cpa']['porcentaje']}%)")
        
        output = {
            "campaign_id": input.campana_id,
            "periodo_1": {
                "descripcion": input.periodo_1,
                "metricas": metricas_1
            },
            "periodo_2": {
                "descripcion": input.periodo_2,
                "metricas": metricas_2
            },
            "deltas": deltas,
            "analisis": " | ".join(analisis) if analisis else "Sin cambios significativos"
        }
        
        logger.info(f"✅ Comparación de períodos completada")
        return CompararPeriodosOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error comparando períodos: {e}")
        return CompararPeriodosOutput(datos_json=json.dumps({"error": str(e)}))


def obtener_metricas_globales_func(input: ObtenerMetricasGlobalesInput) -> ObtenerMetricasGlobalesOutput:
    """
    Obtiene métricas de TODAS las campañas activas.
    
    Returns:
        Métricas agregadas de todas las campañas
    """
    try:
        account = get_account()
        
        date_preset_normalized = normalize_date_preset(input.date_preset)

        params = {
            'date_preset': date_preset_normalized,
            'level': 'campaign',
            'filtering': [
                {'field': 'campaign.effective_status', 'operator': 'IN', 'value': ['ACTIVE', 'PAUSED']}
            ],
            'limit': 200
        }
        
        fields = [
            AdsInsights.Field.campaign_id,
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.ctr,
            AdsInsights.Field.cpm,
            AdsInsights.Field.cpc,
            AdsInsights.Field.actions,
        ]
        
        insights = account.get_insights(fields=fields, params=params)
        
        # Agregar métricas
        total_spend = 0.0
        total_impressions = 0
        total_clicks = 0
        total_conversiones = 0
        campanas_analizadas = 0
        campanas_detalle = []
        
        for insight in insights:
            spend = float(insight.get('spend', 0))
            clicks = int(insight.get('clicks', 0))
            impressions = int(insight.get('impressions', 0))
            
            conversiones = 0
            for action in insight.get('actions', []):
                if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                    conversiones += int(action.get('value', 0))
            
            if spend > 0:
                total_spend += spend
                total_clicks += clicks
                total_impressions += impressions
                total_conversiones += conversiones
                campanas_analizadas += 1
                
                cpa = (spend / conversiones) if conversiones > 0 else 0
                
                campanas_detalle.append({
                    "id": insight.get('campaign_id'),
                    "nombre": insight.get('campaign_name'),
                    "spend": round(spend, 2),
                    "clicks": clicks,
                    "conversiones": conversiones,
                    "cpa": round(cpa, 2)
                })
        
        # Métricas globales
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
        avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        avg_cpa = (total_spend / total_conversiones) if total_conversiones > 0 else 0
        
        # Ordenar campañas por gasto
        campanas_detalle.sort(key=lambda x: x['spend'], reverse=True)
        
        output = {
            "periodo": date_preset_normalized,
            "campanas_analizadas": campanas_analizadas,
            "metricas_globales": {
                "gasto_total_eur": round(total_spend, 2),
                "impresiones_total": total_impressions,
                "clicks_total": total_clicks,
                "ctr_promedio": round(avg_ctr, 2),
                "cpm_promedio": round(avg_cpm, 2),
                "cpc_promedio": round(avg_cpc, 2),
                "conversiones_total": total_conversiones,
                "cpa_promedio": round(avg_cpa, 2)
            },
            "top_campanas": campanas_detalle[:10]
        }
        
        logger.info(f"✅ Métricas globales: {campanas_analizadas} campañas, {total_spend}€")
        return ObtenerMetricasGlobalesOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas globales: {e}")
        return ObtenerMetricasGlobalesOutput(datos_json=json.dumps({"error": str(e)}))
    

def obtener_metricas_por_destino_func(
    input: ObtenerMetricasPorDestinoInput
) -> ObtenerMetricasPorDestinoOutput:
    """
    Obtiene métricas agregadas por destino.
    Responde queries como:
    - "¿Qué destinos funcionaron mejor la semana pasada?"
    - "¿Cuánto se gastó en Costa Blanca en septiembre?"
    
    Returns:
        Métricas por destino con ranking
    """
    try:
        account = get_account()
        
        # 🆕 NORMALIZAR DATE_PRESET
        date_preset_normalized = normalize_date_preset(input.date_preset)

        # Configurar período
        params = {'level': 'adset'}  # Extraemos destino desde adsets
        
        if input.date_start and input.date_end:
            params['time_range'] = {'since': input.date_start, 'until': input.date_end}
            periodo_str = f"{input.date_start} a {input.date_end}"
        else:
            params['date_preset'] = date_preset_normalized  
            periodo_str = date_preset_normalized
        
        fields = [
            AdsInsights.Field.adset_name,
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.actions,
        ]
        
        insights = account.get_insights(fields=fields, params=params)
        
        # Procesar y clasificar por destino
        items = []
        for insight in insights:
            adset_name = insight.get('adset_name', '')
            destination = extract_destination(adset_name)
            
            # Filtrar si se especificó un destino
            if input.destino and destination != input.destino:
                continue
            
            spend = float(insight.get('spend', 0))
            clicks = int(insight.get('clicks', 0))
            impressions = int(insight.get('impressions', 0))
            
            # Extraer conversiones
            conversions = 0
            for action in insight.get('actions', []):
                if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                    conversions += int(action.get('value', 0))
            
            items.append({
                "adset_name": adset_name,
                "destination": destination,
                "spend": spend,
                "clicks": clicks,
                "impressions": impressions,
                "conversions": conversions
            })
        
        # Agregar por destino
        aggregated = aggregate_by_destination(
            items,
            metrics=["spend", "clicks", "impressions", "conversions"]
        )
        
        # Calcular métricas derivadas
        results = []
        for destination, metrics in aggregated.items():
            total_spend = metrics['spend']
            total_clicks = metrics['clicks']
            total_impressions = metrics['impressions']
            total_conversions = metrics['conversions']
            
            ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
            cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
            cpa = (total_spend / total_conversions) if total_conversions > 0 else 0
            
            results.append({
                "destination": destination,
                "spend_eur": round(total_spend, 2),
                "impressions": total_impressions,
                "clicks": total_clicks,
                "conversions": total_conversions,
                "ctr_percentage": round(ctr, 2),
                "cpm_eur": round(cpm, 2),
                "cpc_eur": round(cpc, 2),
                "cpa_eur": round(cpa, 2),
                "adsets_count": metrics['count']
            })
        
        # Ordenar por gasto (mayor a menor)
        results.sort(key=lambda x: x['spend_eur'], reverse=True)
        
        output = {
            "period": periodo_str,
            "total_destinations": len(results),
            "destinations": results
        }
        
        logger.info(f"✅ Métricas por destino: {len(results)} destinos analizados")
        return ObtenerMetricasPorDestinoOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas por destino: {e}")
        return ObtenerMetricasPorDestinoOutput(datos_json=json.dumps({"error": str(e)}))


def obtener_cpa_global_func(
    input: ObtenerCPAGlobalInput
) -> ObtenerCPAGlobalOutput:
    """
    Obtiene CPA global de todas las campañas.
    Responde queries como:
    - "¿Cuál fue el CPA global de las campañas la semana pasada?"
    
    Returns:
        CPA global con métricas agregadas
    """
    try:
        account = get_account()

        date_preset_normalized = normalize_date_preset(input.date_preset)
        
        params = {
            'date_preset': date_preset_normalized,
            'level': 'account'
        }
        
        fields = [
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.actions,
        ]
        
        insights = account.get_insights(fields=fields, params=params)
        
        # Agregar métricas
        total_spend = 0.0
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        
        for insight in insights:
            total_spend += float(insight.get('spend', 0))
            total_impressions += int(insight.get('impressions', 0))
            total_clicks += int(insight.get('clicks', 0))
            
            for action in insight.get('actions', []):
                if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                    total_conversions += int(action.get('value', 0))
        
        # Calcular métricas
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
        cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        cpa = (total_spend / total_conversions) if total_conversions > 0 else 0
        
        output = {
            "period": date_preset_normalized,
            "global_metrics": {
                "total_spend_eur": round(total_spend, 2),
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "global_cpa_eur": round(cpa, 2),
                "global_cpc_eur": round(cpc, 2),
                "global_cpm_eur": round(cpm, 2),
                "global_ctr_percentage": round(ctr, 2)
            }
        }
        
        logger.info(f"✅ CPA global: {cpa:.2f}€")
        return ObtenerCPAGlobalOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo CPA global: {e}")
        return ObtenerCPAGlobalOutput(datos_json=json.dumps({"error": str(e)}))


def obtener_metricas_adset_func(
    input: ObtenerMetricasAdsetInput
) -> ObtenerMetricasAdsetOutput:
    """
    Obtiene métricas a nivel de adset (conjunto de anuncios).
    Responde queries como:
    - "Dame los adsets de la campaña de Baqueira"
    
    Returns:
        Métricas de cada adset con destino clasificado
    """
    try:
        campaign = Campaign(input.campana_id)
        
        date_preset_normalized = normalize_date_preset(input.date_preset)

        params = {
            'date_preset':  date_preset_normalized,
            'level': 'adset'
        }
        
        fields = [
            AdsInsights.Field.adset_id,
            AdsInsights.Field.adset_name,
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.ctr,
            AdsInsights.Field.cpm,
            AdsInsights.Field.cpc,
            AdsInsights.Field.actions,
        ]
        
        insights = campaign.get_insights(fields=fields, params=params)
        
        adsets = []
        for insight in insights:
            adset_name = insight.get('adset_name', '')
            destination = extract_destination(adset_name)
            
            spend = float(insight.get('spend', 0))
            clicks = int(insight.get('clicks', 0))
            
            conversions = 0
            for action in insight.get('actions', []):
                if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                    conversions += int(action.get('value', 0))
            
            cpa = (spend / conversions) if conversions > 0 else 0
            
            adsets.append({
                "adset_id": insight.get('adset_id'),
                "adset_name": adset_name,
                "destination": destination,
                "spend_eur": round(spend, 2),
                "impressions": int(insight.get('impressions', 0)),
                "clicks": clicks,
                "ctr": round(float(insight.get('ctr', 0)), 2),
                "cpm": round(float(insight.get('cpm', 0)), 2),
                "cpc": round(float(insight.get('cpc', 0)), 2),
                "conversions": conversions,
                "cpa": round(cpa, 2)
            })
        
        # Ordenar por gasto
        adsets.sort(key=lambda x: x['spend_eur'], reverse=True)
        
        output = {
            "campaign_id": input.campana_id,
            "period": date_preset_normalized,
            "total_adsets": len(adsets),
            "adsets": adsets
        }
        
        logger.info(f"✅ Métricas de {len(adsets)} adsets obtenidas")
        return ObtenerMetricasAdsetOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas de adsets: {e}")
        return ObtenerMetricasAdsetOutput(datos_json=json.dumps({"error": str(e)}))


def comparar_destinos_func(
    input: CompararDestinosInput
) -> CompararDestinosOutput:
    """
    Compara rendimiento entre múltiples destinos.
    Responde queries como:
    - "Compara Baqueira vs Ibiza vs Costa Blanca"
    
    Returns:
        Comparación lado a lado con ranking
    """
    try:

        date_preset_normalized = normalize_date_preset(input.date_preset)

        # Obtener métricas de todos los destinos
        metricas_input = ObtenerMetricasPorDestinoInput(date_preset=date_preset_normalized)
        result = obtener_metricas_por_destino_func(metricas_input)
        
        all_destinations = json.loads(result.datos_json)['destinations']
        
        # Filtrar solo los destinos solicitados
        filtered = [d for d in all_destinations if d['destination'] in input.destinos]
        
        # Ordenar por CPA (mejor a peor)
        filtered.sort(key=lambda x: x['cpa_eur'])
        
        # Calcular ranking
        for idx, dest in enumerate(filtered, 1):
            dest['rank'] = idx
        
        output = {
            "period": date_preset_normalized,
            "destinations_compared": len(filtered),
            "comparison": filtered,
            "winner": filtered[0]['destination'] if filtered else None
        }
        
        logger.info(f"✅ Comparación de {len(filtered)} destinos completada")
        return CompararDestinosOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error comparando destinos: {e}")
        return CompararDestinosOutput(datos_json=json.dumps({"error": str(e)}))

def obtener_metricas_anuncio_func(input: ObtenerMetricasAnuncioInput) -> ObtenerMetricasAnuncioOutput:
    """
    Obtiene métricas de rendimiento de UN anuncio específico.
    
    Responde queries como:
    - "¿Cómo está el anuncio X?"
    - "Dame métricas del anuncio Y"
    - "¿Qué anuncio ha empeorado?"
    
    Métricas incluidas:
    - Gasto, impresiones, clicks, CTR
    - CPM, CPC, CPA
    - Conversiones (por tipo)
    - Estado del anuncio
    
    Returns:
        Métricas completas del anuncio específico
    """
    try:
        from facebook_business.adobjects.ad import Ad
        
        ad = Ad(input.anuncio_id)
        
        # Normalizar date_preset
        date_preset_normalized = normalize_date_preset(input.date_preset)
        
        # Configurar período
        use_custom = bool(input.date_start and input.date_end)
        params = {'level': 'ad'}
        
        if use_custom:
            params['time_range'] = {'since': input.date_start, 'until': input.date_end}
            periodo_str = f"{input.date_start} a {input.date_end}"
        else:
            params['date_preset'] = date_preset_normalized
            periodo_str = date_preset_normalized
        
        # Campos de insights
        fields = [
            AdsInsights.Field.ad_id,
            AdsInsights.Field.ad_name,
            AdsInsights.Field.adset_id,
            AdsInsights.Field.adset_name,
            AdsInsights.Field.campaign_id,
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.ctr,
            AdsInsights.Field.cpm,
            AdsInsights.Field.cpc,
            AdsInsights.Field.actions,
            AdsInsights.Field.conversions,
        ]
        
        insights = ad.get_insights(fields=fields, params=params)
        
        if not insights:
            # Si no hay insights, obtener info básica del anuncio
            ad_info = ad.api_get(fields=['id', 'name', 'status', 'adset_id', 'campaign_id'])
            return ObtenerMetricasAnuncioOutput(
                datos_json=json.dumps({
                    "ad_id": input.anuncio_id,
                    "ad_name": ad_info.get('name', 'Sin nombre'),
                    "status": ad_info.get('status', 'UNKNOWN'),
                    "adset_id": ad_info.get('adset_id'),
                    "campaign_id": ad_info.get('campaign_id'),
                    "periodo": periodo_str,
                    "error": f"No hay datos para este anuncio en {periodo_str}"
                }, ensure_ascii=False)
            )
        
        # Procesar métricas
        insight = insights[0]  # Solo hay 1 insight para 1 anuncio
        
        spend = float(insight.get('spend', 0))
        impressions = int(insight.get('impressions', 0))
        clicks = int(insight.get('clicks', 0))
        
        # Procesar conversiones
        conversiones_por_tipo = {}
        total_conversiones = 0
        for action in insight.get('actions', []):
            action_type = action.get('action_type')
            value = int(action.get('value', 0))
            conversiones_por_tipo[action_type] = value
            if action_type in ['purchase', 'lead', 'complete_registration']:
                total_conversiones += value
        
        # Calcular métricas derivadas
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cpm = (spend / impressions * 1000) if impressions > 0 else 0
        cpc = (spend / clicks) if clicks > 0 else 0
        cpa = (spend / total_conversiones) if total_conversiones > 0 else 0
        
        output = {
            "ad_id": input.anuncio_id,
            "ad_name": insight.get('ad_name', 'Sin nombre'),
            "adset_id": insight.get('adset_id'),
            "adset_name": insight.get('adset_name'),
            "campaign_id": insight.get('campaign_id'),
            "campaign_name": insight.get('campaign_name'),
            "periodo": periodo_str,
            "metricas": {
                "gasto_eur": round(spend, 2),
                "impresiones": impressions,
                "clicks": clicks,
                "ctr_porcentaje": round(ctr, 2),
                "cpm_eur": round(cpm, 2),
                "cpc_eur": round(cpc, 2),
                "conversiones_total": total_conversiones,
                "conversiones_por_tipo": conversiones_por_tipo,
                "cpa_eur": round(cpa, 2) if total_conversiones > 0 else None
            }
        }
        
        logger.info(f"✅ Métricas del anuncio {input.anuncio_id}: {spend}€, {total_conversiones} conversiones")
        return ObtenerMetricasAnuncioOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas del anuncio: {e}")
        return ObtenerMetricasAnuncioOutput(datos_json=json.dumps({"error": str(e)}))
    
    
def comparar_anuncios_func(input: CompararAnunciosInput) -> CompararAnunciosOutput:
    """
    Compara rendimiento de anuncios de una campaña entre 2 períodos.
    
    Responde queries como:
    - "¿Qué anuncio ha empeorado?"
    - "¿Cuál anuncio explica el aumento del CPA?"
    - "Compara los anuncios de esta semana vs la anterior"
    
    Returns:
        Comparación de anuncios con deltas calculados
    """
    try:
        from facebook_business.adobjects.campaign import Campaign
        
        campaign = Campaign(input.campana_id)
        
        # Función auxiliar para obtener métricas de anuncios en un período
        def obtener_anuncios_periodo(date_preset):
            params = {
                'date_preset': normalize_date_preset(date_preset),
                'level': 'ad'
            }
            
            fields = [
                AdsInsights.Field.ad_id,
                AdsInsights.Field.ad_name,
                AdsInsights.Field.spend,
                AdsInsights.Field.impressions,
                AdsInsights.Field.clicks,
                AdsInsights.Field.ctr,
                AdsInsights.Field.cpm,
                AdsInsights.Field.cpc,
                AdsInsights.Field.actions,
            ]
            
            insights = campaign.get_insights(fields=fields, params=params)
            
            anuncios = {}
            for insight in insights:
                ad_id = insight.get('ad_id')
                spend = float(insight.get('spend', 0))
                clicks = int(insight.get('clicks', 0))
                impressions = int(insight.get('impressions', 0))
                
                # Calcular conversiones
                conversiones = 0
                for action in insight.get('actions', []):
                    if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                        conversiones += int(action.get('value', 0))
                
                ctr = (clicks / impressions * 100) if impressions > 0 else 0
                cpm = (spend / impressions * 1000) if impressions > 0 else 0
                cpc = (spend / clicks) if clicks > 0 else 0
                cpa = (spend / conversiones) if conversiones > 0 else 0
                
                anuncios[ad_id] = {
                    "ad_id": ad_id,
                    "ad_name": insight.get('ad_name'),
                    "spend": round(spend, 2),
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversiones": conversiones,
                    "ctr": round(ctr, 2),
                    "cpm": round(cpm, 2),
                    "cpc": round(cpc, 2),
                    "cpa": round(cpa, 2) if conversiones > 0 else None
                }
            
            return anuncios
        
        # Obtener anuncios de ambos períodos
        anuncios_actual = obtener_anuncios_periodo(input.periodo_actual)
        anuncios_anterior = obtener_anuncios_periodo(input.periodo_anterior)
        
        # Comparar anuncios
        comparacion = []
        for ad_id, datos_actual in anuncios_actual.items():
            if ad_id not in anuncios_anterior:
                # Anuncio nuevo
                comparacion.append({
                    **datos_actual,
                    "status": "NUEVO",
                    "delta_cpa": None,
                    "delta_conversiones": None
                })
                continue
            
            datos_anterior = anuncios_anterior[ad_id]
            
            # Calcular deltas
            delta_cpa = None
            if datos_actual['cpa'] and datos_anterior['cpa']:
                delta_cpa = ((datos_actual['cpa'] - datos_anterior['cpa']) / datos_anterior['cpa']) * 100
            
            delta_conversiones = None
            if datos_anterior['conversiones'] > 0:
                delta_conversiones = ((datos_actual['conversiones'] - datos_anterior['conversiones']) / datos_anterior['conversiones']) * 100
            
            comparacion.append({
                **datos_actual,
                "status": "ACTIVO",
                "periodo_anterior": {
                    "cpa": datos_anterior['cpa'],
                    "conversiones": datos_anterior['conversiones']
                },
                "delta_cpa_porcentaje": round(delta_cpa, 2) if delta_cpa else None,
                "delta_conversiones_porcentaje": round(delta_conversiones, 2) if delta_conversiones else None
            })
        
        # Ordenar según métrica
        metrica_map = {
            "cpa": lambda x: x.get('cpa') or float('inf'),
            "cpc": lambda x: x.get('cpc') or float('inf'),
            "ctr": lambda x: x.get('ctr', 0),
            "conversiones": lambda x: x.get('conversiones', 0)
        }
        
        key_func = metrica_map.get(input.metrica_ordenar, metrica_map["cpa"])
        
        # Para CPA/CPC: mayor = peor (orden descendente)
        # Para CTR/conversiones: menor = peor (orden ascendente)
        reverse = input.metrica_ordenar in ["cpa", "cpc"]
        comparacion.sort(key=key_func, reverse=reverse)
        
        # Identificar peores anuncios
        peores_anuncios = []
        for ad in comparacion[:3]:  # TOP 3 peores
            if ad.get('delta_cpa_porcentaje') and ad['delta_cpa_porcentaje'] > 10:
                peores_anuncios.append({
                    "ad_name": ad['ad_name'],
                    "ad_id": ad['ad_id'],
                    "cpa_actual": ad['cpa'],
                    "cpa_anterior": ad['periodo_anterior']['cpa'],
                    "empeoro_porcentaje": ad['delta_cpa_porcentaje']
                })
        
        output = {
            "campaign_id": input.campana_id,
            "periodo_actual": input.periodo_actual,
            "periodo_anterior": input.periodo_anterior,
            "total_anuncios": len(comparacion),
            "anuncios_empeorados": peores_anuncios,
            "comparacion_completa": comparacion
        }
        
        logger.info(f"✅ Comparación de {len(comparacion)} anuncios completada")
        return CompararAnunciosOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error comparando anuncios: {e}")
        return CompararAnunciosOutput(datos_json=json.dumps({"error": str(e)}))
    

def comparar_anuncios_globales_func(input: CompararAnunciosGlobalesInput) -> CompararAnunciosGlobalesOutput:
    """
    Compara anuncios de TODAS las campañas activas.
    
    Responde queries como:
    - "¿Cómo fueron todas las campañas vs la semana pasada?"
    - "Analiza todos los anuncios de todas las campañas"
    - "¿Qué anuncios empeoraron en general?"
    
    Returns:
        Comparación global con campañas y anuncios que empeoraron
    """
    try:
        account = get_account()
        
        # Obtener todas las campañas activas
        campaigns = account.get_campaigns(
            fields=['id', 'name', 'status'],
            params={
                'effective_status': ['ACTIVE'],
                'limit': input.limite_campanas
            }
        )
        
        resultados_por_campana = []
        total_anuncios_empeorados = 0
        
        for campaign in campaigns:
            try:
                # Usar la función existente para cada campaña
                resultado = comparar_anuncios_func(
                    CompararAnunciosInput(
                        campana_id=campaign['id'],
                        periodo_actual=input.periodo_actual,
                        periodo_anterior=input.periodo_anterior
                    )
                )
                
                datos = json.loads(resultado.datos_json)
                
                # Solo incluir si hay anuncios que empeoraron
                anuncios_empeorados = datos.get('anuncios_empeorados', [])
                if anuncios_empeorados:
                    resultados_por_campana.append({
                        "campaign_id": campaign['id'],
                        "campaign_name": campaign['name'],
                        "anuncios_empeorados": anuncios_empeorados,
                        "total_anuncios": datos.get('total_anuncios', 0)
                    })
                    total_anuncios_empeorados += len(anuncios_empeorados)
            
            except Exception as e:
                logger.debug(f"Error analizando campaña {campaign['id']}: {e}")
                continue
        
        # Ordenar por número de anuncios empeorados
        resultados_por_campana.sort(
            key=lambda x: len(x['anuncios_empeorados']), 
            reverse=True
        )
        
        output = {
            "periodo_actual": input.periodo_actual,
            "periodo_anterior": input.periodo_anterior,
            "total_campanas_analizadas": len(campaigns),
            "campanas_con_problemas": len(resultados_por_campana),
            "total_anuncios_empeorados": total_anuncios_empeorados,
            "resultados_por_campana": resultados_por_campana
        }
        
        logger.info(f"✅ Análisis global: {len(resultados_por_campana)} campañas con anuncios empeorados")
        return CompararAnunciosGlobalesOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error en comparación global: {e}")
        return CompararAnunciosGlobalesOutput(datos_json=json.dumps({"error": str(e)}))

# 🆕 NUEVA FUNCIÓN: Análisis completo del funnel de conversiones
def obtener_funnel_conversiones_func(input: ObtenerFunnelConversionesInput) -> ObtenerFunnelConversionesOutput:
    """
    🆕 NUEVO: Analiza el funnel completo de conversiones (Subscriber → MQL → SQL → Customer).
    
    Responde queries como:
    - "¿Cómo está mi funnel de conversiones?"
    - "Ratio de MQL a SQL de Baqueira"
    - "¿Cuántos subscribers se convirtieron en customers?"
    
    Returns:
        Análisis del funnel con ratios de conversión entre etapas
    """
    try:
        from ..tools.performance.performance_tools import normalize_date_preset
        date_preset_normalized = normalize_date_preset(input.date_preset)
        
        # Configurar período
        use_custom = bool(input.date_start and input.date_end)
        params = {'level': 'campaign' if input.campana_id else 'account'}
        
        if use_custom:
            params['time_range'] = {'since': input.date_start, 'until': input.date_end}
            periodo_str = f"{input.date_start} a {input.date_end}"
        else:
            params['date_preset'] = date_preset_normalized
            periodo_str = date_preset_normalized
        
        fields = [
            AdsInsights.Field.campaign_id,
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.spend,
            AdsInsights.Field.actions,
        ]
        
        # Obtener insights
        if input.campana_id:
            campaign = Campaign(input.campana_id)
            insights = campaign.get_insights(fields=fields, params=params)
        else:
            account = get_account()
            insights = account.get_insights(fields=fields, params=params)
        
        # Agregar conversiones por tipo
        total_spend = 0.0
        funnel_totals = {
            "subscriber": 0,
            "mql": 0,
            "sql": 0,
            "customer": 0,
            "total": 0
        }
        
        for insight in insights:
            total_spend += float(insight.get('spend', 0))
            conversions_by_type = extract_conversion_metrics(insight)
            
            for key in ["subscriber", "mql", "sql", "customer", "total"]:
                funnel_totals[key] += conversions_by_type[key]
        
        # Calcular ratios de conversión
        ratios = {
            "subscriber_to_mql": calculate_conversion_rate(funnel_totals["subscriber"], funnel_totals["mql"]),
            "mql_to_sql": calculate_conversion_rate(funnel_totals["mql"], funnel_totals["sql"]),
            "sql_to_customer": calculate_conversion_rate(funnel_totals["sql"], funnel_totals["customer"]),
            "subscriber_to_customer": calculate_conversion_rate(funnel_totals["subscriber"], funnel_totals["customer"])
        }
        
        # Calcular CPAs por etapa
        cpas = {
            "cpa_subscriber": round(total_spend / funnel_totals["subscriber"], 2) if funnel_totals["subscriber"] > 0 else None,
            "cpa_mql": round(total_spend / funnel_totals["mql"], 2) if funnel_totals["mql"] > 0 else None,
            "cpa_sql": round(total_spend / funnel_totals["sql"], 2) if funnel_totals["sql"] > 0 else None,
            "cpa_customer": round(total_spend / funnel_totals["customer"], 2) if funnel_totals["customer"] > 0 else None,
        }
        
        # Análisis cualitativo
        analisis = []
        
        if ratios["mql_to_sql"] < 30:
            analisis.append(f"⚠️ Ratio MQL→SQL bajo ({ratios['mql_to_sql']}%). Objetivo: >30%")
        elif ratios["mql_to_sql"] >= 50:
            analisis.append(f"✅ Excelente ratio MQL→SQL ({ratios['mql_to_sql']}%)")
        
        if ratios["sql_to_customer"] < 20:
            analisis.append(f"⚠️ Ratio SQL→Customer bajo ({ratios['sql_to_customer']}%). Objetivo: >20%")
        elif ratios["sql_to_customer"] >= 40:
            analisis.append(f"✅ Excelente ratio SQL→Customer ({ratios['sql_to_customer']}%)")
        
        if funnel_totals["mql"] == 0:
            analisis.append("🚨 No hay MQLs registrados. Verifica tracking de eventos.")
        
        if funnel_totals["sql"] == 0:
            analisis.append("🚨 No hay SQLs registrados. Verifica tracking de eventos.")
        
        output = {
            "campaign_id": input.campana_id or "global",
            "periodo": periodo_str,
            "gasto_total_eur": round(total_spend, 2),
            "funnel": {
                "subscriber": funnel_totals["subscriber"],
                "mql": funnel_totals["mql"],
                "sql": funnel_totals["sql"],
                "customer": funnel_totals["customer"],
                "total_conversiones": funnel_totals["total"]
            },
            "ratios_conversion": ratios,
            "cpa_por_etapa": cpas,
            "analisis": analisis,
            "recomendaciones": [
                "📊 Ratio MQL→SQL ideal: >30%",
                "🎯 Ratio SQL→Customer ideal: >20%",
                "💰 CPA más bajo en etapas tempranas es esperado"
            ]
        }
        
        logger.info(
            f"✅ Análisis del funnel: "
            f"Subs:{funnel_totals['subscriber']} → MQL:{funnel_totals['mql']} → "
            f"SQL:{funnel_totals['sql']} → Customers:{funnel_totals['customer']}"
        )
        
        return ObtenerFunnelConversionesOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error analizando funnel: {e}")
        return ObtenerFunnelConversionesOutput(datos_json=json.dumps({"error": str(e)}))

