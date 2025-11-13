"""
Inicialización de la API de Meta/Facebook Business
"""

import logging
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

from ..config.settings import settings

logger = logging.getLogger(__name__)

# Variable global para la API
_api_initialized = False


def init_api():
    """Inicializa la API de Facebook Business."""
    global _api_initialized
    
    if _api_initialized:
        return
    
    try:
        FacebookAdsApi.init(
            app_id=settings.META_APP_ID,
            app_secret=settings.META_APP_SECRET,
            access_token=settings.META_ACCESS_TOKEN
        )
        _api_initialized = True
        logger.info("✅ API de Meta Ads inicializada correctamente")
    except Exception as e:
        logger.error(f"❌ Error inicializando Meta Ads API: {e}")
        raise


def get_account():
    """Retorna la instancia de AdAccount después de inicializar la API."""
    if not _api_initialized:
        init_api()
    
    return AdAccount(fbid=settings.AD_ACCOUNT_ID)


# Inicializar automáticamente al importar (opcional)
try:
    init_api()
except Exception as e:
    logger.warning(f"⚠️ No se pudo inicializar API al importar: {e}")