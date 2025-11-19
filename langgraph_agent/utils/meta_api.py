"""
Utilidades para Meta Ads API
Gestión de autenticación y conexión
"""

import logging
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from ..config.settings import settings

logger = logging.getLogger(__name__)

# Variable global para cachear la instancia de API
_meta_api_instance = None
_ad_account_instance = None


def initialize_meta_api() -> FacebookAdsApi:
    """
    Inicializa la API de Facebook/Meta Ads.
    Solo se ejecuta una vez (singleton pattern).
    
    Returns:
        FacebookAdsApi instance
        
    Raises:
        ValueError: Si faltan credenciales
    """
    global _meta_api_instance
    
    if _meta_api_instance is not None:
        return _meta_api_instance
    
    # Validar credenciales
    if not settings.META_ACCESS_TOKEN:
        raise ValueError("META_ACCESS_TOKEN no configurado en .env")
    
    if not settings.META_AD_ACCOUNT_ID:
        raise ValueError("META_AD_ACCOUNT_ID no configurado en .env")
    
    try:
        # Inicializar API
        api = FacebookAdsApi.init(
            access_token=settings.META_ACCESS_TOKEN,
            api_version=settings.META_API_VERSION
        )
        
        _meta_api_instance = api
        
        logger.info(f"✅ Meta Ads API inicializada (v{settings.META_API_VERSION})")
        logger.info(f"   Account ID: {settings.META_AD_ACCOUNT_ID}")
        
        return api
    
    except Exception as e:
        logger.error(f"❌ Error inicializando Meta Ads API: {e}")
        raise


def get_account() -> AdAccount:
    """
    Obtiene la instancia de AdAccount configurada.
    Usa caché para evitar reinicializar.
    
    Returns:
        AdAccount instance
        
    Example:
        >>> account = get_account()
        >>> campaigns = account.get_campaigns()
    """
    global _ad_account_instance
    
    if _ad_account_instance is not None:
        return _ad_account_instance
    
    # Inicializar API si no está inicializada
    if _meta_api_instance is None:
        initialize_meta_api()
    
    try:
        # Crear instancia de AdAccount
        account = AdAccount(settings.META_AD_ACCOUNT_ID)
        
        _ad_account_instance = account
        
        logger.info(f"✅ AdAccount instanciado: {settings.META_AD_ACCOUNT_ID}")
        
        return account
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo AdAccount: {e}")
        raise


def reset_api_connection():
    """
    Resetea la conexión a la API (útil para testing o reconexión).
    """
    global _meta_api_instance, _ad_account_instance
    
    _meta_api_instance = None
    _ad_account_instance = None
    
    logger.info("🔄 Conexión Meta API reseteada")


def test_connection() -> bool:
    """
    Prueba la conexión a Meta Ads API.
    
    Returns:
        True si la conexión es exitosa, False en caso contrario
    """
    try:
        account = get_account()
        
        # Intentar obtener 1 campaña para validar permisos
        campaigns = account.get_campaigns(
            fields=['id', 'name'],
            params={'limit': 1}
        )
        
        # Forzar ejecución de la query
        list(campaigns)
        
        logger.info("✅ Conexión Meta Ads API verificada")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error en test de conexión: {e}")
        return False


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing Meta API Connection...\n")
    
    # Test 1: Inicializar API
    print("1. Inicializando API...")
    try:
        api = initialize_meta_api()
        print(f"   ✅ API inicializada: {api}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        exit(1)
    
    # Test 2: Obtener AdAccount
    print("\n2. Obteniendo AdAccount...")
    try:
        account = get_account()
        print(f"   ✅ AdAccount: {account.get_id()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        exit(1)
    
    # Test 3: Test de conexión
    print("\n3. Probando conexión...")
    if test_connection():
        print("   ✅ Conexión exitosa")
    else:
        print("   ❌ Conexión fallida")
        exit(1)
    
    # Test 4: Obtener 1 campaña
    print("\n4. Obteniendo 1 campaña de prueba...")
    try:
        campaigns = account.get_campaigns(
            fields=['id', 'name', 'status'],
            params={'limit': 1}
        )
        
        for camp in campaigns:
            print(f"   ✅ Campaña: {camp.get('name')} (ID: {camp.get('id')})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Todos los tests pasaron\n")