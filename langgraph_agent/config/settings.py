"""
Settings Centralizados
Variables de configuración y mapeos
"""

import os
from typing import Dict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración global de la aplicación"""
    
    # ========== META ADS API ==========
    META_ACCESS_TOKEN: str = os.getenv("META_ACCESS_TOKEN", "")
    META_AD_ACCOUNT_ID: str = os.getenv("META_AD_ACCOUNT_ID", "")
    META_API_VERSION: str = "v19.0"
    
    # ========== GOOGLE AI ==========
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    
    # ========== LANGCHAIN ==========
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "meta-ads-agent-v5")
    
    # ========== SERVER ==========
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # ========== MAPEOS ==========
    
    # Mapeo de estrategias de puja (código técnico → legible)
    BID_STRATEGY_MAP: Dict[str, str] = {
        "LOWEST_COST_WITHOUT_CAP": "Costo más bajo (sin límite)",
        "LOWEST_COST_WITH_BID_CAP": "Costo más bajo (con límite de puja)",
        "COST_CAP": "Límite de costo",
        "LOWEST_COST_WITH_MIN_ROAS": "Costo más bajo (con ROAS mínimo)",
    }
    
    # Mapeo de destinos (nombre corto → nombre completo)
    # Usado en buscar_campana_por_nombre_func() para normalizar nombres
    DESTINO_MAPPING: Dict[str, str] = {
        # Montaña
        "baqueira": "baqueira",
        "andorra": "andorra",
        "pirineos": "pirineos",
        
        # Islas
        "ibiza": "ibiza",
        "mallorca": "mallorca",
        "menorca": "menorca",
        "canarias": "canarias",
        
        # Costas
        "cantabria": "cantabria",
        "costa luz": "costaluz",
        "costa de la luz": "costaluz",
        "costa blanca": "costablanca",
        "costa del sol": "costasol",
        "costa sol": "costasol",
    }
    
    # Tipos de conversiones consideradas como válidas
    CONVERSION_ACTION_TYPES: list = [
        "purchase",
        "lead",
        "complete_registration",
        "add_to_cart",
        "initiate_checkout",
    ]
    
    # Límites de rate limiting
    MAX_CAMPAIGNS_PER_REQUEST: int = 50
    MAX_ADS_PER_REQUEST: int = 100
    
    # Timeouts
    META_API_TIMEOUT: int = 30  # segundos
    LLM_TIMEOUT: int = 60  # segundos
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# ========== INSTANCIA GLOBAL ==========

settings = Settings()


# ========== VALIDACIÓN AL IMPORTAR ==========

def validate_settings():
    """Valida que las configuraciones críticas existan"""
    errors = []
    
    if not settings.META_ACCESS_TOKEN:
        errors.append("❌ META_ACCESS_TOKEN no configurado")
    
    if not settings.META_AD_ACCOUNT_ID:
        errors.append("❌ META_AD_ACCOUNT_ID no configurado")
    
    if not (settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY):
        errors.append("❌ GOOGLE_API_KEY o GEMINI_API_KEY no configurado")
    
    if errors:
        print("\n⚠️ ADVERTENCIAS DE CONFIGURACIÓN:")
        for error in errors:
            print(f"  {error}")
        print()
    else:
        print("✅ Configuración validada correctamente")


# Validar al importar (opcional, comentar si molesta)
# validate_settings()