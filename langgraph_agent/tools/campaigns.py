"""Herramientas para gestión de campañas"""

import json
import logging
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet

from ..models.schemas import (
    ListarCampanasInput, ListarCampanasOutput,
    BuscarIdCampanaInput, BuscarIdCampanaOutput
)
from ..utils.meta_api import get_account
from ..config.settings import settings

logger = logging.getLogger(__name__)


def listar_campanas_func(input: ListarCampanasInput) -> ListarCampanasOutput:
    """Lista todas las campañas de la cuenta"""
    try:
        account = get_account()
        campanas = account.get_campaigns(fields=['id', 'name', 'status'])
        campanas_data = [
            {"id": c['id'], "name": c['name'], "status": c.get('status')}
            for c in campanas
        ]
        return ListarCampanasOutput(campanas_json=json.dumps(campanas_data))
    except Exception as e:
        logger.error(f"Error listando campañas: {e}")
        return ListarCampanasOutput(campanas_json=json.dumps({"error": str(e)}))


def buscar_id_campana_func(input: BuscarIdCampanaInput) -> BuscarIdCampanaOutput:
    """Busca campaña por nombre con mapeo de destinos"""
    
    # 🔧 NORMALIZAR INPUT: Puede llegar como dict o como objeto Pydantic
    if isinstance(input, dict):
        nombre_buscado = input.get('nombre_campana', '').lower()
    else:
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
                return BuscarIdCampanaOutput(
                    id_campana=camp.get(Campaign.Field.id),
                    nombre_encontrado=camp.get(Campaign.Field.name)
                )
        
        # Buscar en adsets
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
                        return BuscarIdCampanaOutput(
                            id_campana=camp.get(Campaign.Field.id),
                            nombre_encontrado=f"{camp.get(Campaign.Field.name)} (destino: {nombre_buscado})"
                        )
            except:
                continue
        
        return BuscarIdCampanaOutput(
            id_campana="None",
            nombre_encontrado=f"No encontrado: '{nombre_buscado}'"
        )
    
    except Exception as e:
        logger.error(f"Error buscando campaña: {e}")
        return BuscarIdCampanaOutput(id_campana="None", nombre_encontrado=f"Error: {str(e)}")