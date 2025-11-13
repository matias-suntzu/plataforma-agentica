"""Herramientas para gestión de anuncios"""

import json
import time
import logging
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.exceptions import FacebookRequestError

from models.schemas import (
    ObtenerAnunciosPorRendimientoInput,
    ObtenerAnunciosPorRendimientoOutput
)
from utils.meta_api import get_account
from utils.helpers import safe_int_from_insight

logger = logging.getLogger(__name__)


def obtener_anuncios_por_rendimiento_func(
    input: ObtenerAnunciosPorRendimientoInput
) -> ObtenerAnunciosPorRendimientoOutput:
    """
    Obtiene anuncios por rendimiento con métricas detalladas.
    Incluye retry logic para rate limiting.
    """
    # Normalizar input
    if isinstance(input, dict):
        campana_id = input.get('campana_id', '')
        date_preset = input.get('date_preset')
        date_start = input.get('date_start')
        date_end = input.get('date_end')
        limite = input.get('limite', 3)
    else:
        campana_id = input.campana_id
        date_preset = input.date_preset
        date_start = input.date_start
        date_end = input.date_end
        limite = input.limite

    use_custom_range = bool(date_start and date_end)
    periodo_str = f"{date_start} a {date_end}" if use_custom_range else (date_preset or 'last_7d')

    if use_custom_range:
        date_preset = None
    elif not date_preset:
        date_preset = 'last_7d'

    try:
        campaign = Campaign(campana_id)
        
        # Campos de insights
        insight_fields = [
            AdsInsights.Field.ad_id, AdsInsights.Field.ad_name,
            AdsInsights.Field.clicks, AdsInsights.Field.impressions,
            AdsInsights.Field.spend, AdsInsights.Field.ctr,
            AdsInsights.Field.cpm, AdsInsights.Field.cpc,
            AdsInsights.Field.actions, AdsInsights.Field.reach,
            AdsInsights.Field.frequency, AdsInsights.Field.inline_link_clicks,
            AdsInsights.Field.inline_link_click_ctr,
            AdsInsights.Field.outbound_clicks, AdsInsights.Field.outbound_clicks_ctr,
            AdsInsights.Field.cost_per_inline_link_click,
            AdsInsights.Field.cost_per_outbound_click,
            AdsInsights.Field.cost_per_unique_click,
            AdsInsights.Field.conversions, AdsInsights.Field.conversion_values,
            AdsInsights.Field.cost_per_conversion,
        ]

        # Parámetros de la consulta
        params = {'level': 'ad'}
        if use_custom_range:
            params['time_range'] = {'since': date_start, 'until': date_end}
        else:
            params['date_preset'] = date_preset

        params = {k: v for k, v in params.items() if v is not None and v != {}}

        # Retry logic para rate limiting
        retry_attempts = 3
        ads_insights = None
        
        for attempt in range(retry_attempts):
            try:
                ads_insights = campaign.get_insights(fields=insight_fields, params=params)
                break
            except FacebookRequestError as fb_err:
                if fb_err.api_error_code() == 4:
                    logger.warning(f"⏳ Límite de API alcanzado. Reintentando en 5s... (Intento {attempt + 1}/{retry_attempts})")
                    time.sleep(5)
                    continue
                else:
                    raise fb_err
        else:
            return ObtenerAnunciosPorRendimientoOutput(
                datos_json=json.dumps({
                    "error": "Se alcanzó el límite de llamadas de la API de Meta. Intenta más tarde."
                })
            )

        if not ads_insights:
            return ObtenerAnunciosPorRendimientoOutput(
                datos_json=json.dumps({
                    "error": f"No hay datos para campaña {campana_id} en {periodo_str}"
                })
            )

        # Procesar insights
        resultados = []
        totals = {
            'spend': 0.0, 'clicks': 0, 'impressions': 0,
            'conversions': 0, 'reach': 0, 'inline_link_clicks': 0,
            'outbound_clicks': 0
        }

        for insight in ads_insights:
            # Extraer métricas básicas
            clicks = safe_int_from_insight(insight.get(AdsInsights.Field.clicks))
            impressions = safe_int_from_insight(insight.get(AdsInsights.Field.impressions))
            spend = float(insight.get(AdsInsights.Field.spend, 0.0))
            ctr = float(insight.get(AdsInsights.Field.ctr, 0.0))
            cpm = float(insight.get(AdsInsights.Field.cpm, 0.0))
            cpc = float(insight.get(AdsInsights.Field.cpc, 0.0))
            reach = safe_int_from_insight(insight.get(AdsInsights.Field.reach))
            frequency = float(insight.get(AdsInsights.Field.frequency, 0.0))
            
            # Métricas de enlace
            inline_link_clicks = safe_int_from_insight(insight.get(AdsInsights.Field.inline_link_clicks))
            outbound_clicks = safe_int_from_insight(insight.get(AdsInsights.Field.outbound_clicks))
            inline_link_click_ctr = float(insight.get(AdsInsights.Field.inline_link_click_ctr, 0.0))
            outbound_clicks_ctr = safe_int_from_insight(insight.get(AdsInsights.Field.outbound_clicks_ctr, 0.0))
            cost_per_inline_link_click = float(insight.get(AdsInsights.Field.cost_per_inline_link_click, 0.0))
            cost_per_outbound_click = safe_int_from_insight(insight.get(AdsInsights.Field.cost_per_outbound_click, 0.0))
            cost_per_unique_click = float(insight.get(AdsInsights.Field.cost_per_unique_click, 0.0))

            # Procesar conversiones
            conversions = 0
            conversion_value = 0.0
            
            for action in insight.get(AdsInsights.Field.actions, []):
                if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                    conversions += int(action.get('value', 0))
            
            conversions_direct = insight.get(AdsInsights.Field.conversions)
            if conversions_direct:
                for conv in conversions_direct:
                    conversions += int(conv.get('value', 0))
            
            conversion_values = insight.get(AdsInsights.Field.conversion_values)
            if conversion_values:
                for cv in conversion_values:
                    conversion_value += float(cv.get('value', 0))
            
            cost_per_conversion = safe_int_from_insight(insight.get(AdsInsights.Field.cost_per_conversion, 0.0))
            cpa = spend / conversions if conversions > 0 else 0.0

            # Actualizar totales
            totals['spend'] += spend
            totals['clicks'] += clicks
            totals['impressions'] += impressions
            totals['conversions'] += conversions
            totals['reach'] += reach
            totals['inline_link_clicks'] += inline_link_clicks
            totals['outbound_clicks'] += outbound_clicks

            # Agregar resultado
            resultados.append({
                "ad_id": insight.get(AdsInsights.Field.ad_id, 'N/A'),
                "ad_name": insight.get(AdsInsights.Field.ad_name, 'Sin nombre'),
                "clicks": clicks,
                "impressions": impressions,
                "spend": round(spend, 2),
                "ctr": round(ctr, 2),
                "cpm": round(cpm, 2),
                "cpc": round(cpc, 2),
                "reach": reach,
                "frequency": round(frequency, 2),
                "inline_link_clicks": inline_link_clicks,
                "inline_link_click_ctr": round(inline_link_click_ctr, 2),
                "outbound_clicks": outbound_clicks,
                "outbound_clicks_ctr": round(outbound_clicks_ctr, 2),
                "cost_per_inline_link_click": round(cost_per_inline_link_click, 2),
                "cost_per_outbound_click": round(cost_per_outbound_click, 2),
                "cost_per_unique_click": round(cost_per_unique_click, 2),
                "conversiones": conversions,
                "conversion_value": round(conversion_value, 2),
                "cost_per_conversion": round(cost_per_conversion, 2),
                "cpa": round(cpa, 2),
            })

        # Ordenar por clicks y limitar
        top_anuncios = sorted(resultados, key=lambda x: x['clicks'], reverse=True)[:limite]
        
        output = {
            "metadata": {
                "report_title": f"Top {len(top_anuncios)} Anuncios - Campaña {campana_id}",
                "periodo": periodo_str
            },
            "data": top_anuncios
        }
        
        return ObtenerAnunciosPorRendimientoOutput(datos_json=json.dumps(output))

    except FacebookRequestError as fb_err:
        msg = fb_err.api_error_message()
        logger.error(f"Error de API de Facebook: {msg}", exc_info=True)
        return ObtenerAnunciosPorRendimientoOutput(datos_json=json.dumps({"error": msg}))

    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        return ObtenerAnunciosPorRendimientoOutput(datos_json=json.dumps({"error": str(e)}))

