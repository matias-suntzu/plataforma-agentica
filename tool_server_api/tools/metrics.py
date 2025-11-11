"""Herramientas para métricas globales"""

import json
import logging
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights

from models.schemas import (
    GetAllCampaignsMetricsInput,
    GetAllCampaignsMetricsOutput
)
from config.settings import settings

logger = logging.getLogger(__name__)


def get_all_campaigns_metrics_func(
    input: GetAllCampaignsMetricsInput
) -> GetAllCampaignsMetricsOutput:
    """
    OPTIMIZADO: Obtiene métricas clave de todas las campañas activas/pausadas
    usando UNA sola llamada a nivel de AdAccount para evitar timeouts.
    """
    logger.info("⚙️ Llamando a la herramienta: Obtener Métricas de Campañas (OPTIMIZADO)")
    
    # Obtener date_preset
    date_preset = input.date_preset if isinstance(input, GetAllCampaignsMetricsInput) else input.get('date_preset', 'last_7d')
    
    try:
        # 1. Definir campos
        fields = [
            AdsInsights.Field.campaign_id,
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.spend,
            AdsInsights.Field.clicks,
            AdsInsights.Field.impressions,
            AdsInsights.Field.actions
        ]
        
        # 2. Parámetros de consulta
        params = {
            'date_preset': date_preset,
            'level': 'campaign',
            'filtering': [
                {'field': 'campaign.effective_status', 'operator': 'IN', 'value': ['ACTIVE', 'PAUSED']}
            ],
            'limit': 200,
            'time_increment': 1
        }
        
        # 3. Ejecutar llamada a nivel de cuenta (MÁS RÁPIDO)
        account = AdAccount(fbid=settings.AD_ACCOUNT_ID)
        insights = account.get_insights(fields=fields, params=params)
        
        logger.info(f"   Debug: Insights recibidos: {len(insights)} registros.")
        
        # 4. Procesar y agregar resultados
        totals = {
            'total_spend': 0.0,
            'total_clicks': 0,
            'total_impressions': 0,
            'total_conversions': 0,
            'campaigns_analyzed': 0,
            'campaigns': [],
            'period': date_preset
        }
        
        # Diccionario para agregar por campaña
        campaign_map = {}

        for insight in insights:
            camp_id = insight.get('campaign_id')
            if camp_id not in campaign_map:
                campaign_map[camp_id] = {
                    'id': camp_id,
                    'name': insight.get('campaign_name', 'N/A'),
                    'spend': 0.0,
                    'clicks': 0,
                    'impressions': 0,
                    'conversions': 0,
                }
            
            # Agregación
            spend = float(insight.get('spend', 0))
            clicks = int(insight.get('clicks', 0))
            impressions = int(insight.get('impressions', 0))
            
            conversions = 0
            for action in insight.get('actions', []):
                if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                    conversions += int(action.get('value', 0))
            
            campaign_map[camp_id]['spend'] += spend
            campaign_map[camp_id]['clicks'] += clicks
            campaign_map[camp_id]['impressions'] += impressions
            campaign_map[camp_id]['conversions'] += conversions

        # 5. Calcular totales y métricas finales
        for camp_id, data in campaign_map.items():
            camp_spend = data['spend']
            camp_conversions = data['conversions']
            
            if camp_spend > 0:
                totals['total_spend'] += camp_spend
                totals['total_clicks'] += data['clicks']
                totals['total_impressions'] += data['impressions']
                totals['total_conversions'] += camp_conversions
                totals['campaigns_analyzed'] += 1
                
                camp_cpa = (camp_spend / camp_conversions) if camp_conversions > 0 else 0
                
                totals['campaigns'].append({
                    'id': camp_id,
                    'name': data['name'],
                    'spend': round(camp_spend, 2),
                    'clicks': data['clicks'],
                    'conversions': camp_conversions,
                    'cpa': round(camp_cpa, 2)
                })
        
        # Calcular promedios
        if totals['total_clicks'] > 0:
            totals['avg_cpc'] = round(totals['total_spend'] / totals['total_clicks'], 2)
        else:
            totals['avg_cpc'] = 0
            
        if totals['total_conversions'] > 0:
            totals['avg_cpa'] = round(totals['total_spend'] / totals['total_conversions'], 2)
        else:
            totals['avg_cpa'] = 0
            
        if totals['total_impressions'] > 0:
            totals['avg_ctr'] = round((totals['total_clicks'] / totals['total_impressions']) * 100, 2)
        else:
            totals['avg_ctr'] = 0
        
        # Ordenar campañas por gasto
        totals['campaigns'].sort(key=lambda x: x['spend'], reverse=True)
        
        logger.info(f"✅ Métricas globales: {totals['campaigns_analyzed']} campañas, {totals['total_spend']}€")
        return GetAllCampaignsMetricsOutput(datos_json=json.dumps(totals))
    
    except Exception as e:
        error_message = f"Error Crítico al consultar Meta Ads: {str(e)}"
        logger.error(error_message, exc_info=True)
        return GetAllCampaignsMetricsOutput(datos_json=json.dumps({
            "error": "Error al consultar la API de Meta Ads. Revisa el log del servidor para el detalle técnico.",
            "detalle_tecnico": error_message
        }))