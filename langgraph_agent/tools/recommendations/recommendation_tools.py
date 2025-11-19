"""
Herramientas de Recomendaciones
Responsabilidad: Analizar configuración y sugerir optimizaciones
"""

import json
import logging
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet

from ...models.schemas import BaseModel, Field
from ...utils.meta_api import get_account
from ...config.settings import settings

logger = logging.getLogger(__name__)


# ========== SCHEMAS ==========

class ObtenerRecomendacionesInput(BaseModel):
    """Obtiene recomendaciones de optimización para una campaña"""
    campana_id: str = Field(
        default="None",
        description="ID de la campaña (None = todas las activas)"
    )
    incluir_prioridad_baja: bool = Field(
        default=False,
        description="Incluir recomendaciones de baja prioridad"
    )


class ObtenerRecomendacionesOutput(BaseModel):
    """Salida con recomendaciones priorizadas"""
    datos_json: str


class AnalizarOpportunidadInput(BaseModel):
    """Analiza oportunidades de mejora específicas"""
    campana_id: str = Field(description="ID de la campaña")
    tipo_analisis: str = Field(
        default="all",
        description="Tipo: 'advantage_plus', 'budget', 'targeting', 'all'"
    )


class AnalizarOpportunidadOutput(BaseModel):
    """Salida con análisis detallado"""
    datos_json: str


# ========== FUNCIONES ==========

def obtener_recomendaciones_func(
    input: ObtenerRecomendacionesInput
) -> ObtenerRecomendacionesOutput:
    """
    Obtiene recomendaciones de optimización basadas en configuración actual.
    
    Analiza:
    - Advantage+ Audience (¿está activado?)
    - Presupuestos (¿son suficientes?)
    - Targeting (¿muy amplio o estrecho?)
    
    Returns:
        Recomendaciones priorizadas con puntuación de oportunidad
    """
    try:
        account = get_account()
        
        # Determinar campañas a analizar
        if input.campana_id == "None":
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
            campaign_obj = Campaign(input.campana_id)
            campaign_data = campaign_obj.api_get(fields=['name'])
            campaign_ids = [(input.campana_id, campaign_data.get('name', 'Sin nombre'))]
        
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
                    adset_id = adset.get(AdSet.Field.id)
                    daily_budget = adset.get(AdSet.Field.daily_budget)
                    targeting = adset.get(AdSet.Field.targeting, {})
                    
                    # 🔍 RECOMENDACIÓN 1: Advantage+ no activado (ALTA PRIORIDAD)
                    advantage_custom_audience = targeting.get('advantage_custom_audience')
                    if not advantage_custom_audience or advantage_custom_audience == 'off':
                        recommendations.append({
                            "type": "advantage_plus_audience",
                            "adset": adset_name,
                            "adset_id": adset_id,
                            "title": "Activar Advantage+ Audience puede mejorar el rendimiento",
                            "description": "Meta optimizará automáticamente la entrega a las personas con mayor probabilidad de conversión",
                            "potential_improvement": "9.7% reducción en costo por resultado",
                            "action": f"Activar Advantage+ Audience en el adset '{adset_name}'",
                            "points": 3,
                            "priority": "high"
                        })
                        opportunity_score += 3
                    
                    # 🔍 RECOMENDACIÓN 2: Presupuesto bajo (MEDIA PRIORIDAD)
                    if daily_budget:
                        daily_budget_eur = float(daily_budget) / 100
                        if daily_budget_eur < 10:
                            recommendations.append({
                                "type": "low_budget",
                                "adset": adset_name,
                                "adset_id": adset_id,
                                "title": f"Presupuesto diario bajo ({daily_budget_eur:.2f}€)",
                                "description": "Presupuestos bajos limitan el alcance y la capacidad de aprendizaje del algoritmo",
                                "potential_improvement": "Aumentar a mínimo 10€/día para mejor rendimiento",
                                "action": f"Aumentar presupuesto del adset '{adset_name}' a 10€/día",
                                "points": 2,
                                "priority": "medium",
                                "current_budget_eur": daily_budget_eur
                            })
                            opportunity_score += 2
                    
                    # 🔍 RECOMENDACIÓN 3: Targeting muy amplio (BAJA PRIORIDAD)
                    age_min = targeting.get('age_min', 18)
                    age_max = targeting.get('age_max', 65)
                    age_range = age_max - age_min
                    
                    if age_range > 40:
                        if input.incluir_prioridad_baja:
                            recommendations.append({
                                "type": "broad_targeting",
                                "adset": adset_name,
                                "adset_id": adset_id,
                                "title": f"Targeting de edad muy amplio ({age_min}-{age_max} años)",
                                "description": "Segmentar por grupos de edad puede mejorar la relevancia",
                                "potential_improvement": "Segmentar en rangos de 10-15 años",
                                "action": f"Crear duplicados del adset con rangos: 18-34, 35-54, 55+",
                                "points": 1,
                                "priority": "low"
                            })
                            opportunity_score += 1
                    
                    # 🔍 RECOMENDACIÓN 4: Targeting muy estrecho (BAJA PRIORIDAD)
                    elif age_range < 10:
                        if input.incluir_prioridad_baja:
                            recommendations.append({
                                "type": "narrow_targeting",
                                "adset": adset_name,
                                "adset_id": adset_id,
                                "title": f"Targeting de edad muy estrecho ({age_min}-{age_max} años)",
                                "description": "Audiencias pequeñas limitan el alcance potencial",
                                "potential_improvement": "Ampliar rango para mayor alcance",
                                "action": f"Ampliar rango a {age_min}-{min(age_max + 10, 65)} años",
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
                        "total_recommendations": len(recommendations),
                        "high_priority": len([r for r in recommendations if r['priority'] == 'high']),
                        "medium_priority": len([r for r in recommendations if r['priority'] == 'medium']),
                        "low_priority": len([r for r in recommendations if r['priority'] == 'low']),
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
        
        logger.info(
            f"✅ Recomendaciones: {len(all_recommendations)} campañas "
            f"con {total_opportunity_score} puntos de oportunidad"
        )
        
        return ObtenerRecomendacionesOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones: {e}")
        return ObtenerRecomendacionesOutput(datos_json=json.dumps({"error": str(e)}))


def analizar_oportunidad_func(
    input: AnalizarOpportunidadInput
) -> AnalizarOpportunidadOutput:
    """
    Analiza oportunidades de mejora específicas para una campaña.
    
    Tipos de análisis:
    - 'advantage_plus': Solo Advantage+ Audience
    - 'budget': Solo presupuestos
    - 'targeting': Solo targeting
    - 'all': Todos los análisis
    
    Returns:
        Análisis detallado con métricas de impacto
    """
    try:
        campaign = Campaign(input.campana_id)
        campaign_data = campaign.api_get(fields=['name'])
        
        adsets = campaign.get_ad_sets(
            fields=[
                AdSet.Field.name,
                AdSet.Field.id,
                AdSet.Field.daily_budget,
                AdSet.Field.targeting,
                AdSet.Field.status,
            ],
            params={'effective_status': ['ACTIVE']}
        )
        
        analysis = {
            "campaign_id": input.campana_id,
            "campaign_name": campaign_data.get('name'),
            "total_adsets": 0,
            "insights": {}
        }
        
        # Contadores
        adsets_sin_advantage = []
        adsets_bajo_presupuesto = []
        adsets_targeting_amplio = []
        adsets_targeting_estrecho = []
        
        for adset in adsets:
            analysis["total_adsets"] += 1
            
            adset_info = {
                "id": adset.get(AdSet.Field.id),
                "name": adset.get(AdSet.Field.name)
            }
            
            targeting = adset.get(AdSet.Field.targeting, {})
            daily_budget = adset.get(AdSet.Field.daily_budget)
            
            # Análisis Advantage+
            if input.tipo_analisis in ['advantage_plus', 'all']:
                advantage = targeting.get('advantage_custom_audience')
                if not advantage or advantage == 'off':
                    adsets_sin_advantage.append(adset_info)
            
            # Análisis Presupuesto
            if input.tipo_analisis in ['budget', 'all']:
                if daily_budget:
                    daily_budget_eur = float(daily_budget) / 100
                    if daily_budget_eur < 10:
                        adsets_bajo_presupuesto.append({
                            **adset_info,
                            "current_budget": daily_budget_eur
                        })
            
            # Análisis Targeting
            if input.tipo_analisis in ['targeting', 'all']:
                age_min = targeting.get('age_min', 18)
                age_max = targeting.get('age_max', 65)
                age_range = age_max - age_min
                
                if age_range > 40:
                    adsets_targeting_amplio.append({
                        **adset_info,
                        "age_range": f"{age_min}-{age_max}"
                    })
                elif age_range < 10:
                    adsets_targeting_estrecho.append({
                        **adset_info,
                        "age_range": f"{age_min}-{age_max}"
                    })
        
        # Construir insights
        if adsets_sin_advantage:
            analysis["insights"]["advantage_plus"] = {
                "total_adsets_affected": len(adsets_sin_advantage),
                "potential_improvement": "9.7% reducción en CPA",
                "priority": "high",
                "adsets": adsets_sin_advantage
            }
        
        if adsets_bajo_presupuesto:
            analysis["insights"]["budget"] = {
                "total_adsets_affected": len(adsets_bajo_presupuesto),
                "potential_improvement": "Mayor alcance y capacidad de aprendizaje",
                "priority": "medium",
                "adsets": adsets_bajo_presupuesto
            }
        
        if adsets_targeting_amplio:
            analysis["insights"]["targeting_broad"] = {
                "total_adsets_affected": len(adsets_targeting_amplio),
                "potential_improvement": "Mayor relevancia y mejor segmentación",
                "priority": "low",
                "adsets": adsets_targeting_amplio
            }
        
        if adsets_targeting_estrecho:
            analysis["insights"]["targeting_narrow"] = {
                "total_adsets_affected": len(adsets_targeting_estrecho),
                "potential_improvement": "Mayor alcance potencial",
                "priority": "low",
                "adsets": adsets_targeting_estrecho
            }
        
        logger.info(f"✅ Análisis de oportunidad completado para {input.campana_id}")
        return AnalizarOpportunidadOutput(datos_json=json.dumps(analysis, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error analizando oportunidad: {e}")
        return AnalizarOpportunidadOutput(datos_json=json.dumps({"error": str(e)}))