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

from typing import List

logger = logging.getLogger(__name__)


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
    """Obtiene TOP N anuncios de una campaña"""
    campana_id: str = Field(description="ID de la campaña")
    date_preset: str = Field(default="last_7d", description="Período")
    date_start: str = Field(default=None, description="Fecha inicio")
    date_end: str = Field(default=None, description="Fecha fin")
    limite: int = Field(default=3, description="TOP N anuncios")


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


# ========== FUNCIONES ==========

def obtener_metricas_campana_func(input: ObtenerMetricasCampanaInput) -> ObtenerMetricasCampanaOutput:
    """
    Obtiene métricas de rendimiento de UNA campaña específica.
    
    Métricas incluidas:
    - Gasto total
    - Impresiones, clicks, CTR
    - CPM, CPC
    - Conversiones (por tipo), CPA
    - Ratio de conversiones
    """
    try:
        campaign = Campaign(input.campana_id)
        
        # Configurar período
        use_custom = bool(input.date_start and input.date_end)
        params = {'level': 'campaign'}
        
        if use_custom:
            params['time_range'] = {'since': input.date_start, 'until': input.date_end}
            periodo_str = f"{input.date_start} a {input.date_end}"
        else:
            params['date_preset'] = input.date_preset
            periodo_str = input.date_preset
        
        # Campos de insights
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
        
        # Agregar métricas
        total_spend = 0.0
        total_impressions = 0
        total_clicks = 0
        conversiones_por_tipo = {}
        valor_conversion_total = 0.0
        
        for insight in insights:
            total_spend += float(insight.get('spend', 0))
            total_impressions += int(insight.get('impressions', 0))
            total_clicks += int(insight.get('clicks', 0))
            
            # Procesar conversiones
            for action in insight.get('actions', []):
                action_type = action.get('action_type')
                value = int(action.get('value', 0))
                conversiones_por_tipo[action_type] = conversiones_por_tipo.get(action_type, 0) + value
            
            # Valor de conversiones
            for cv in insight.get('conversion_values', []):
                valor_conversion_total += float(cv.get('value', 0))
        
        # Calcular métricas derivadas
        total_conversiones = sum(conversiones_por_tipo.values())
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
        cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        cpa = (total_spend / total_conversiones) if total_conversiones > 0 else 0
        ratio_conversion = (total_conversiones / total_clicks * 100) if total_clicks > 0 else 0
        valor_por_coste = (valor_conversion_total / total_spend) if total_spend > 0 else 0
        
        output = {
            "campaign_id": input.campana_id,
            "periodo": periodo_str,
            "metricas": {
                "gasto_total_eur": round(total_spend, 2),
                "impresiones": total_impressions,
                "clicks": total_clicks,
                "ctr_porcentaje": round(ctr, 2),
                "cpm_eur": round(cpm, 2),
                "cpc_eur": round(cpc, 2),
                "conversiones_total": total_conversiones,
                "conversiones_por_tipo": conversiones_por_tipo,
                "cpa_eur": round(cpa, 2),
                "ratio_conversion_porcentaje": round(ratio_conversion, 2),
                "valor_conversion_total_eur": round(valor_conversion_total, 2),
                "valor_por_coste_ratio": round(valor_por_coste, 2)
            }
        }
        
        logger.info(f"✅ Métricas de campaña {input.campana_id}: {total_spend}€, {total_conversiones} conversiones")
        return ObtenerMetricasCampanaOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas: {e}")
        return ObtenerMetricasCampanaOutput(datos_json=json.dumps({"error": str(e)}))


def obtener_anuncios_por_rendimiento_func(input: ObtenerAnunciosPorRendimientoInput) -> ObtenerAnunciosPorRendimientoOutput:
    """
    Obtiene TOP N anuncios de una campaña ordenados por clicks.
    
    Returns:
        Lista de anuncios con métricas completas
    """
    try:
        campaign = Campaign(input.campana_id)
        
        # Configurar período
        use_custom = bool(input.date_start and input.date_end)
        params = {'level': 'ad'}
        
        if use_custom:
            params['time_range'] = {'since': input.date_start, 'until': input.date_end}
        else:
            params['date_preset'] = input.date_preset
        
        # Campos de insights
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
        
        # Procesar anuncios
        anuncios = []
        for insight in insights:
            conversiones = 0
            for action in insight.get('actions', []):
                if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                    conversiones += int(action.get('value', 0))
            
            spend = float(insight.get('spend', 0))
            clicks = int(insight.get('clicks', 0))
            cpa = (spend / conversiones) if conversiones > 0 else 0
            
            anuncios.append({
                "ad_id": insight.get('ad_id'),
                "ad_name": insight.get('ad_name', 'Sin nombre'),
                "spend_eur": round(spend, 2),
                "impressions": int(insight.get('impressions', 0)),
                "clicks": clicks,
                "ctr": round(float(insight.get('ctr', 0)), 2),
                "cpm": round(float(insight.get('cpm', 0)), 2),
                "cpc": round(float(insight.get('cpc', 0)), 2),
                "conversiones": conversiones,
                "cpa": round(cpa, 2)
            })
        
        # Ordenar por clicks y limitar
        top_anuncios = sorted(anuncios, key=lambda x: x['clicks'], reverse=True)[:input.limite]
        
        output = {
            "campaign_id": input.campana_id,
            "top_n": len(top_anuncios),
            "anuncios": top_anuncios
        }
        
        logger.info(f"✅ TOP {len(top_anuncios)} anuncios de campaña {input.campana_id}")
        return ObtenerAnunciosPorRendimientoOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo anuncios: {e}")
        return ObtenerAnunciosPorRendimientoOutput(datos_json=json.dumps({"error": str(e)}))


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
            
            if periodo == 'custom' and fecha_inicio and fecha_fin:
                params['time_range'] = {'since': fecha_inicio, 'until': fecha_fin}
            elif periodo == 'last_7d':
                params['date_preset'] = 'last_7d'
            elif periodo == 'this_week':
                # Lunes de esta semana hasta hoy
                hoy = datetime.now()
                lunes = hoy - timedelta(days=hoy.weekday())
                params['time_range'] = {
                    'since': lunes.strftime('%Y-%m-%d'),
                    'until': hoy.strftime('%Y-%m-%d')
                }
            elif periodo == 'last_week':
                # Semana pasada completa
                hoy = datetime.now()
                lunes_pasado = hoy - timedelta(days=hoy.weekday() + 7)
                domingo_pasado = lunes_pasado + timedelta(days=6)
                params['time_range'] = {
                    'since': lunes_pasado.strftime('%Y-%m-%d'),
                    'until': domingo_pasado.strftime('%Y-%m-%d')
                }
            elif periodo == 'previous_7d':
                # 7 días anteriores a los últimos 7
                hoy = datetime.now()
                fin = hoy - timedelta(days=7)
                inicio = fin - timedelta(days=7)
                params['time_range'] = {
                    'since': inicio.strftime('%Y-%m-%d'),
                    'until': fin.strftime('%Y-%m-%d')
                }
            else:
                params['date_preset'] = periodo
            
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
        
        params = {
            'date_preset': input.date_preset,
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
            "periodo": input.date_preset,
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
        
        # Configurar período
        params = {'level': 'adset'}  # Extraemos destino desde adsets
        
        if input.date_start and input.date_end:
            params['time_range'] = {'since': input.date_start, 'until': input.date_end}
            periodo_str = f"{input.date_start} a {input.date_end}"
        else:
            params['date_preset'] = input.date_preset
            periodo_str = input.date_preset
        
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
        
        params = {
            'date_preset': input.date_preset,
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
            "period": input.date_preset,
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
        
        params = {
            'date_preset': input.date_preset,
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
            "period": input.date_preset,
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
        # Obtener métricas de todos los destinos
        metricas_input = ObtenerMetricasPorDestinoInput(date_preset=input.date_preset)
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
            "period": input.date_preset,
            "destinations_compared": len(filtered),
            "comparison": filtered,
            "winner": filtered[0]['destination'] if filtered else None
        }
        
        logger.info(f"✅ Comparación de {len(filtered)} destinos completada")
        return CompararDestinosOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error comparando destinos: {e}")
        return CompararDestinosOutput(datos_json=json.dumps({"error": str(e)}))
