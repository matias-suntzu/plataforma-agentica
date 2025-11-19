"""
Herramientas de Configuración de Campañas
Responsabilidad: Información técnica, presupuestos, estrategias
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

class ListarCampanasInput(BaseModel):
    """Lista todas las campañas"""
    estado: str = Field(
        default="ACTIVE,PAUSED",
        description="Estados a filtrar: ACTIVE, PAUSED, ARCHIVED"
    )
    limite: int = Field(default=50, description="Máximo de campañas a listar")


class ListarCampanasOutput(BaseModel):
    """Salida con lista de campañas"""
    campanas_json: str


class BuscarCampanaPorNombreInput(BaseModel):
    """Busca campaña por nombre o parte del nombre"""
    nombre_campana: str = Field(description="Nombre o parte del nombre de la campaña")


class BuscarCampanaPorNombreOutput(BaseModel):
    """Salida con ID y nombre de campaña encontrada"""
    id_campana: str
    nombre_encontrado: str


class ObtenerDetallesCampanaInput(BaseModel):
    """Obtiene detalles técnicos completos de una campaña"""
    campana_id: str = Field(description="ID de la campaña")
    incluir_adsets: bool = Field(default=True, description="Incluir detalles de adsets")


class ObtenerDetallesCampanaOutput(BaseModel):
    """Salida con configuración completa"""
    datos_json: str


class ObtenerPresupuestoInput(BaseModel):
    """Obtiene información de presupuesto de una campaña"""
    campana_id: str = Field(description="ID de la campaña")


class ObtenerPresupuestoOutput(BaseModel):
    """Salida con presupuestos"""
    datos_json: str


class ObtenerEstrategiaPujaInput(BaseModel):
    """Obtiene estrategia de puja de una campaña"""
    campana_id: str = Field(description="ID de la campaña")


class ObtenerEstrategiaPujaOutput(BaseModel):
    """Salida con estrategia de puja"""
    datos_json: str


# ========== FUNCIONES ==========

def listar_campanas_func(input: ListarCampanasInput) -> ListarCampanasOutput:
    """
    Lista todas las campañas de la cuenta con filtros de estado.
    
    Returns:
        Lista de campañas con ID, nombre y estado
    """
    try:
        account = get_account()
        
        # Parsear estados
        estados = input.estado.split(',')
        
        campanas = account.get_campaigns(
            fields=[
                Campaign.Field.id,
                Campaign.Field.name,
                Campaign.Field.status,
                Campaign.Field.objective,
            ],
            params={
                'effective_status': estados,
                'limit': input.limite
            }
        )
        
        campanas_data = []
        for c in campanas:
            campanas_data.append({
                "id": c.get(Campaign.Field.id),
                "nombre": c.get(Campaign.Field.name),
                "estado": c.get(Campaign.Field.status),
                "objetivo": c.get(Campaign.Field.objective, 'N/A')
            })
        
        logger.info(f"✅ {len(campanas_data)} campañas listadas")
        return ListarCampanasOutput(campanas_json=json.dumps(campanas_data, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error listando campañas: {e}")
        return ListarCampanasOutput(campanas_json=json.dumps({"error": str(e)}))


def buscar_campana_por_nombre_func(input: BuscarCampanaPorNombreInput) -> BuscarCampanaPorNombreOutput:
    """
    Busca una campaña por nombre (búsqueda parcial).
    Aplica mapeo de destinos automáticamente.
    
    Returns:
        ID y nombre de la campaña encontrada
    """
    nombre_buscado = input.nombre_campana.lower()
    
    # Aplicar mapeo de destinos
    nombre_normalizado = settings.DESTINO_MAPPING.get(nombre_buscado, nombre_buscado)
    
    try:
        account = get_account()
        campaigns = account.get_campaigns(
            fields=[Campaign.Field.name, Campaign.Field.id],
            params={'effective_status': ['ACTIVE', 'PAUSED'], 'limit': 100}
        )
        
        # Buscar en nombres de campaña
        for camp in campaigns:
            camp_name = camp.get(Campaign.Field.name, "").lower()
            if nombre_normalizado in camp_name or nombre_buscado in camp_name:
                logger.info(f"✅ Campaña encontrada: {camp.get(Campaign.Field.name)}")
                return BuscarCampanaPorNombreOutput(
                    id_campana=camp.get(Campaign.Field.id),
                    nombre_encontrado=camp.get(Campaign.Field.name)
                )
        
        # Buscar en adsets si no se encuentra en campañas
        for camp in campaigns:
            try:
                campaign_obj = Campaign(camp.get(Campaign.Field.id))
                adsets = campaign_obj.get_ad_sets(
                    fields=[AdSet.Field.name, AdSet.Field.id],
                    params={'effective_status': ['ACTIVE', 'PAUSED']}
                )
                
                for adset in adsets:
                    adset_name = adset.get(AdSet.Field.name, "").lower()
                    if nombre_normalizado in adset_name:
                        logger.info(f"✅ Campaña encontrada vía adset: {camp.get(Campaign.Field.name)}")
                        return BuscarCampanaPorNombreOutput(
                            id_campana=camp.get(Campaign.Field.id),
                            nombre_encontrado=f"{camp.get(Campaign.Field.name)} (via adset: {nombre_buscado})"
                        )
            except:
                continue
        
        logger.warning(f"⚠️ No se encontró campaña con nombre: {nombre_buscado}")
        return BuscarCampanaPorNombreOutput(
            id_campana="None",
            nombre_encontrado=f"No encontrado: '{nombre_buscado}'"
        )
    
    except Exception as e:
        logger.error(f"❌ Error buscando campaña: {e}")
        return BuscarCampanaPorNombreOutput(
            id_campana="None",
            nombre_encontrado=f"Error: {str(e)}"
        )


def obtener_detalles_campana_func(input: ObtenerDetallesCampanaInput) -> ObtenerDetallesCampanaOutput:
    """
    Obtiene detalles técnicos completos de una campaña:
    - Objetivo, estado, estrategia de puja
    - Presupuestos (diario, lifetime, restante)
    - Configuración de adsets (targeting, optimización)
    
    Returns:
        Configuración completa en JSON
    """
    try:
        campaign = Campaign(input.campana_id)
        
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
        
        # Procesar presupuestos (centavos a euros)
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
            "campaign_id": input.campana_id,
            "nombre": campaign_data.get(Campaign.Field.name, 'Sin nombre'),
            "estado": campaign_data.get(Campaign.Field.status, 'UNKNOWN'),
            "objetivo": campaign_data.get(Campaign.Field.objective, 'N/A'),
            "estrategia_puja": bid_strategy_readable,
            "estrategia_puja_code": bid_strategy,
            "presupuesto": {
                "diario_eur": round(daily_budget_eur, 2) if daily_budget_eur else None,
                "lifetime_eur": round(lifetime_budget_eur, 2) if lifetime_budget_eur else None,
                "restante_eur": round(budget_remaining_eur, 2) if budget_remaining_eur else None,
            },
            "adsets": []
        }
        
        # Obtener adsets si se solicita
        if input.incluir_adsets:
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
                    "nombre": adset.get(AdSet.Field.name, 'Sin nombre'),
                    "estado": adset.get(AdSet.Field.status, 'UNKNOWN'),
                    "presupuesto_diario_eur": round(adset_budget_eur, 2) if adset_budget_eur else None,
                    "objetivo_optimizacion": adset.get(AdSet.Field.optimization_goal, 'N/A'),
                    "advantage_plus_activado": advantage_enabled,
                    "targeting": {
                        "rango_edad": f"{age_min}-{age_max}",
                        "generos": gender_str,
                        "paises": countries,
                    }
                })
        
        logger.info(f"✅ Detalles de campaña {input.campana_id}: {len(output['adsets'])} adsets")
        return ObtenerDetallesCampanaOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalles: {e}")
        return ObtenerDetallesCampanaOutput(datos_json=json.dumps({"error": str(e)}))


def obtener_presupuesto_func(input: ObtenerPresupuestoInput) -> ObtenerPresupuestoOutput:
    """
    Obtiene SOLO información de presupuestos de una campaña.
    Más rápido que obtener_detalles_campana_func.
    
    Returns:
        Presupuestos (diario, lifetime, restante) en EUR
    """
    try:
        campaign = Campaign(input.campana_id)
        
        campaign_data = campaign.api_get(
            fields=[
                Campaign.Field.name,
                Campaign.Field.daily_budget,
                Campaign.Field.lifetime_budget,
                Campaign.Field.budget_remaining,
            ]
        )
        
        # Convertir a EUR
        daily_budget = campaign_data.get(Campaign.Field.daily_budget)
        lifetime_budget = campaign_data.get(Campaign.Field.lifetime_budget)
        budget_remaining = campaign_data.get(Campaign.Field.budget_remaining)
        
        output = {
            "campaign_id": input.campana_id,
            "nombre": campaign_data.get(Campaign.Field.name),
            "presupuesto_diario_eur": round(float(daily_budget) / 100, 2) if daily_budget else None,
            "presupuesto_lifetime_eur": round(float(lifetime_budget) / 100, 2) if lifetime_budget else None,
            "presupuesto_restante_eur": round(float(budget_remaining) / 100, 2) if budget_remaining else None,
        }
        
        logger.info(f"✅ Presupuesto de {output['nombre']}: {output['presupuesto_diario_eur']}€/día")
        return ObtenerPresupuestoOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo presupuesto: {e}")
        return ObtenerPresupuestoOutput(datos_json=json.dumps({"error": str(e)}))


def obtener_estrategia_puja_func(input: ObtenerEstrategiaPujaInput) -> ObtenerEstrategiaPujaOutput:
    """
    Obtiene SOLO la estrategia de puja de una campaña.
    Más rápido que obtener_detalles_campana_func.
    
    Returns:
        Estrategia de puja legible y código técnico
    """
    try:
        campaign = Campaign(input.campana_id)
        
        campaign_data = campaign.api_get(
            fields=[
                Campaign.Field.name,
                Campaign.Field.bid_strategy,
            ]
        )
        
        bid_strategy = campaign_data.get(Campaign.Field.bid_strategy, 'LOWEST_COST_WITHOUT_CAP')
        bid_strategy_readable = settings.BID_STRATEGY_MAP.get(bid_strategy, bid_strategy)
        
        output = {
            "campaign_id": input.campana_id,
            "nombre": campaign_data.get(Campaign.Field.name),
            "estrategia_puja": bid_strategy_readable,
            "estrategia_puja_code": bid_strategy,
        }
        
        logger.info(f"✅ Estrategia de {output['nombre']}: {bid_strategy_readable}")
        return ObtenerEstrategiaPujaOutput(datos_json=json.dumps(output, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo estrategia: {e}")
        return ObtenerEstrategiaPujaOutput(datos_json=json.dumps({"error": str(e)}))


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing Config Tools...\n")
    
    # Test 1: Listar campañas
    print("1. Listar campañas...")
    try:
        result = listar_campanas_func(ListarCampanasInput(limite=5))
        campanas = json.loads(result.campanas_json)
        print(f"   ✅ {len(campanas)} campañas encontradas")
        for camp in campanas[:3]:
            print(f"      - {camp['nombre']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Buscar campaña
    print("\n2. Buscar campaña por nombre...")
    try:
        result = buscar_campana_por_nombre_func(
            BuscarCampanaPorNombreInput(nombre_campana="baqueira")
        )
        print(f"   ✅ Encontrada: {result.nombre_encontrado}")
        print(f"      ID: {result.id_campana}")
        
        # Test 3: Obtener presupuesto
        if result.id_campana != "None":
            print("\n3. Obtener presupuesto...")
            presupuesto_result = obtener_presupuesto_func(
                ObtenerPresupuestoInput(campana_id=result.id_campana)
            )
            presupuesto = json.loads(presupuesto_result.datos_json)
            print(f"   ✅ Presupuesto diario: {presupuesto.get('presupuesto_diario_eur')}€")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Tests completados\n")