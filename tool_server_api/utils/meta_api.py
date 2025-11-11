"""Inicialización y gestión de Meta Ads API"""

import logging
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from config.settings import settings

logger = logging.getLogger(__name__)

# Variable global para la cuenta
account = None


def init_meta_api():
    """
    Inicializa Meta Ads API y retorna la cuenta.
    Solo se ejecuta una vez (singleton pattern).
    """
    global account
    
    try:
        if settings.ACCESS_TOKEN:
            FacebookAdsApi.init(
                app_id=settings.APP_ID,
                app_secret=settings.APP_SECRET,
                access_token=settings.ACCESS_TOKEN
            )
            account = AdAccount(settings.AD_ACCOUNT_ID)
            logger.info(f"✅ Meta Ads API inicializada: {settings.AD_ACCOUNT_ID}")
            return account
        else:
            logger.error("❌ ACCESS_TOKEN no configurado en .env")
            return None
    
    except Exception as e:
        logger.error(f"❌ Error inicializando Meta Ads API: {e}")
        return None


def get_account():
    """
    Retorna la cuenta inicializada (lazy loading).
    Si no está inicializada, la inicializa automáticamente.
    """
    global account
    
    if account is None:
        account = init_meta_api()
    
    return account