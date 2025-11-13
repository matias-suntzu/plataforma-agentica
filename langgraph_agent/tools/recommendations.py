"""Herramientas para recomendaciones y detalles de campaña"""

import json
import logging
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet

from models.schemas import (
    GetCampaignRecommendationsInput,
    GetCampaignRecommendationsOutput,
    GetCampaignDetailsInput,
    GetCampaignDetailsOutput
)
from utils.meta_api import get_account
from config.settings import settings

logger = logging.getLogger(__name__)


def get_campaign_recommendations_func(
    input: GetCampaignRecommendationsInput
) -> GetCampaignRecommendationsOutput:
    """
    Obtiene recomendaciones de optimización para una campaña específica o todas las campañas.
    Analiza configuración de adsets y genera puntuación de oportunidad.
    
    🔧 OPTIMIZADO: Reduce llamadas a la API de Meta
    """
    campana_id = input.campana_id if isinstance(input, GetCampaignRecommendationsInput) else input.get('campana_id')
    
    try:
        account = get_account()
        
        # Si no hay campana_id, analizar todas (pero limitar a activas)
        if not campana_id or campana_id == "None":
            campaigns = account.get_campaigns(
                fields=['id', 'name', 'status'],
                params={
                    'effective_status': ['ACTIVE'],
                    'limit': 50
                }
            )
            campaign_ids = [(c['id'], c['name']) for c in campaigns]
            
            logger.info(f"🔍 Analizando {len(campaign_ids)} campañas activas...")
        else:
            campaign_obj = Campaign(campana_id)
            campaign_data = campaign_obj.api_get(fields=['name'])
            campaign_ids = [(campana_id, campaign_data.get('name', 'Sin nombre'))]
        
        all_recommendations = []
        total_opportunity_score = 0
        
        for camp_id, camp_name in campaign_ids:
            try:
                campaign = Campaign(camp_id)
                
                # Obtener adsets con configuración completa
                adsets = campaign.get_ad_sets(
                    fields=[
                        AdSet.Field.name,
                        AdSet.Field.id,
                        AdSet.Field.daily_budget,
                        AdSet.Field.lifetime_budget,
                        AdSet.Field.optimization_goal,
                        AdSet.Field.bid_strategy,
                        AdSet.Field.targeting,
                        AdSet.Field.status,
                    ],
                    params={'effective_status': ['ACTIVE']}
                )
                
                recommendations = []
                opportunity_score = 0
                
                for adset in adsets:
                    adset_name = adset.get(AdSet.Field.name, '')
                    daily_budget = adset.get(AdSet.Field.daily_budget)
                    targeting = adset.get(AdSet.Field.targeting, {})
                    
                    # 🔍 RECOMENDACIÓN 1: Advantage+ no activado
                    advantage_custom_audience = targeting.get('advantage_custom_audience')
                    if not advantage_custom_audience or advantage_custom_audience == 'off':
                        recommendations.append({
                            "type": "advantage_plus_audience",
                            "adset": adset_name,
                            "adset_id": adset.get(AdSet.Field.id),
                            "title": "Activar Advantage+ Audience puede mejorar el rendimiento",
                            "potential_improvement": "9.7% reducción en costo por resultado",
                            "points": 2,
                            "priority": "high"
                        })
                        opportunity_score += 2
                    
                    # 🔍 RECOMENDACIÓN 2: Presupuesto bajo
                    if daily_budget:
                        daily_budget_eur = float(daily_budget) / 100
                        if daily_budget_eur < 10:
                            recommendations.append({
                                "type": "low_budget",
                                "adset": adset_name,
                                "adset_id": adset.get(AdSet.Field.id),
                                "title": f"Presupuesto diario bajo ({daily_budget_eur}€)",
                                "potential_improvement": "Aumentar a mínimo 10€/día",
                                "points": 1,
                                "priority": "medium",
                                "current_budget_eur": daily_budget_eur
                            })
                            opportunity_score += 1
                    
                    # 🔍 RECOMENDACIÓN 3: Targeting muy amplio o estrecho
                    age_min = targeting.get('age_min', 18)
                    age_max = targeting.get('age_max', 65)
                    age_range = age_max - age_min
                    
                    if age_range > 40:
                        recommendations.append({
                            "type": "broad_targeting",
                            "adset": adset_name,
                            "adset_id": adset.get(AdSet.Field.id),
                            "title": f"Targeting de edad muy amplio ({age_min}-{age_max} años)",
                            "potential_improvement": "Segmentar por grupos de edad",
                            "points": 1,
                            "priority": "low"
                        })
                        opportunity_score += 1
                    elif age_range < 10:
                        recommendations.append({
                            "type": "narrow_targeting",
                            "adset": adset_name,
                            "adset_id": adset.get(AdSet.Field.id),
                            "title": f"Targeting de edad muy estrecho ({age_min}-{age_max} años)",
                            "potential_improvement": "Ampliar rango para mayor alcance",
                            "points": 1,
                            "priority": "low"
                        })
                        opportunity_score += 1
                
                # Solo agregar si tiene recomendaciones
                if recommendations:
                    all_recommendations.append({
                        "campaign_id": camp_id,
                        "campaign_name": camp_name,
                        "opportunity_score": opportunity_score,
                        "recommendations": recommendations
                    })
                    total_opportunity_score += opportunity_score
                
            except Exception as e:
                logger.debug(f"Sin datos para campaña {camp_id}: {e}")
                continue
        
        # Ordenar por puntuación (mayor a menor)
        all_recommendations.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        output = {
            "total_campaigns_analyzed": len(campaign_ids),
            "campaigns_with_opportunities": len(all_recommendations),
            "total_opportunity_score": total_opportunity_score,
            "recommendations_by_campaign": all_recommendations
        }
        
        logger.info(f"✅ Recomendaciones: {len(all_recommendations)} campañas con {total_opportunity_score} puntos")
        return GetCampaignRecommendationsOutput(datos_json=json.dumps(output))
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return GetCampaignRecommendationsOutput(datos_json=json.dumps({"error": str(e)}))


def get_campaign_details_func(
    input: GetCampaignDetailsInput
) -> GetCampaignDetailsOutput:
    """
    Obtiene detalles técnicos completos de una campaña:
    - Estrategia de puja
    - Presupuestos
    - Configuración de adsets (targeting, optimization goal)
    """
    if isinstance(input, dict):
        campana_id = input.get('campana_id', '')
        include_adsets = input.get('include_adsets', True)
    else:
        campana_id = input.campana_id
        include_adsets = input.include_adsets
    
    try:
        campaign = Campaign(campana_id)
        
        # Obtener datos de campaña
        campaign_data = campaign.api_get(
            fields=[
                Campaign.Field.name,
                Campaign.Field.status,
                Campaign.Field.objective,
                Campaign.Field.daily_budget,
                Campaign.Field.lifetime_budget,
                Campaign.Field.budget_remaining,
                Campaign.Field.bid_strategy,
            ]
        )
        
        # Procesar presupuestos (convertir centavos a euros)
        daily_budget = campaign_data.get(Campaign.Field.daily_budget)
        lifetime_budget = campaign_data.get(Campaign.Field.lifetime_budget)
        budget_remaining = campaign_data.get(Campaign.Field.budget_remaining)
        
        daily_budget_eur = float(daily_budget) / 100 if daily_budget else None
        lifetime_budget_eur = float(lifetime_budget) / 100 if lifetime_budget else None
        budget_remaining_eur = float(budget_remaining) / 100 if budget_remaining else None
        
        # Estrategia de puja
        bid_strategy = campaign_data.get(Campaign.Field.bid_strategy, 'LOWEST_COST_WITHOUT_CAP')
        bid_strategy_readable = settings.BID_STRATEGY_MAP.get(bid_strategy, bid_strategy)
        
        output = {
            "campaign_id": campana_id,
            "campaign_name": campaign_data.get(Campaign.Field.name, 'Sin nombre'),
            "status": campaign_data.get(Campaign.Field.status, 'UNKNOWN'),
            "objective": campaign_data.get(Campaign.Field.objective, 'N/A'),
            "bid_strategy": bid_strategy_readable,
            "bid_strategy_code": bid_strategy,
            "budget": {
                "daily_budget_eur": round(daily_budget_eur, 2) if daily_budget_eur else None,
                "lifetime_budget_eur": round(lifetime_budget_eur, 2) if lifetime_budget_eur else None,
                "budget_remaining_eur": round(budget_remaining_eur, 2) if budget_remaining_eur else None,
            },
            "adsets": []
        }
        
        # Obtener adsets si se solicita
        if include_adsets:
            adsets = campaign.get_ad_sets(
                fields=[
                    AdSet.Field.name,
                    AdSet.Field.id,
                    AdSet.Field.status,
                    AdSet.Field.daily_budget,
                    AdSet.Field.optimization_goal,
                    AdSet.Field.bid_strategy,
                    AdSet.Field.targeting,
                ],
                params={'effective_status': ['ACTIVE', 'PAUSED']}
            )
            
            for adset in adsets:
                targeting = adset.get(AdSet.Field.targeting, {})
                
                # Extraer configuración de targeting
                age_min = targeting.get('age_min', 'N/A')
                age_max = targeting.get('age_max', 'N/A')
                genders = targeting.get('genders', [])
                gender_str = "Todos" if not genders else ", ".join([str(g) for g in genders])
                
                geo_locations = targeting.get('geo_locations', {})
                countries = geo_locations.get('countries', [])
                
                # Advantage+ activado
                advantage_custom_audience = targeting.get('advantage_custom_audience', 'off')
                advantage_enabled = advantage_custom_audience != 'off'
                
                adset_budget = adset.get(AdSet.Field.daily_budget)
                adset_budget_eur = float(adset_budget) / 100 if adset_budget else None
                
                output["adsets"].append({
                    "adset_id": adset.get(AdSet.Field.id),
                    "adset_name": adset.get(AdSet.Field.name, 'Sin nombre'),
                    "status": adset.get(AdSet.Field.status, 'UNKNOWN'),
                    "daily_budget_eur": round(adset_budget_eur, 2) if adset_budget_eur else None,
                    "optimization_goal": adset.get(AdSet.Field.optimization_goal, 'N/A'),
                    "advantage_plus_enabled": advantage_enabled,
                    "targeting": {
                        "age_range": f"{age_min}-{age_max}",
                        "genders": gender_str,
                        "countries": countries,
                    }
                })
        
        logger.info(f"✅ Detalles de campaña {campana_id}: {len(output['adsets'])} adsets")
        return GetCampaignDetailsOutput(datos_json=json.dumps(output))
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return GetCampaignDetailsOutput(datos_json=json.dumps({"error": str(e)}))
