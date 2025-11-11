"""Variables de entorno y configuración centralizada"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuración centralizada del servidor"""
    
    # ========== META ADS ==========
    AD_ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID', 'act_952835605437684')
    ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
    APP_ID = os.getenv('META_APP_ID')
    APP_SECRET = os.getenv('META_APP_SECRET')
    
    # ========== SEGURIDAD ==========
    TOOL_API_KEY = os.getenv("TOOL_API_KEY", "53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG").strip()
    
    # ========== INTEGRACIONES ==========
    N8N_WEBHOOK_URL = os.getenv(
        'N8N_SLIDES_WEBHOOK_URL',
        'http://localhost:5678/webhook/generar-reporte-meta-ads'
    )
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
    
    # ========== MAPEOS DE DATOS ==========
    DESTINO_MAPPING = {
        'baqueira': 'baqueira',
        'ibiza': 'ibiza',
        'menorca': 'menorca',
        'costa del sol': 'costasol',
        'costasol': 'costasol',
        'costa de la luz': 'costaluz',
        'costaluz': 'costaluz',
        'costa blanca': 'costablanca',
        'costablanca': 'costablanca',
        'cantabria': 'cantabria',
        'formentera': 'formentera'
    }
    
    BID_STRATEGY_MAP = {
        'LOWEST_COST_WITHOUT_CAP': 'Volumen más alto',
        'COST_CAP': 'Objetivo de costo por resultado',
        'LOWEST_COST_WITH_BID_CAP': 'Límite de costo',
        'TARGET_COST': 'Objetivo de costo',
    }
    
    # ========== VALIDACIÓN ==========
    @classmethod
    def validate(cls):
        """Valida que las configuraciones críticas estén presentes"""
        errors = []
        
        if not cls.ACCESS_TOKEN:
            errors.append("❌ META_ACCESS_TOKEN no configurado")
        
        if not cls.APP_ID:
            errors.append("❌ META_APP_ID no configurado")
        
        if not cls.APP_SECRET:
            errors.append("❌ META_APP_SECRET no configurado")
        
        if errors:
            print("\n⚠️ ERRORES DE CONFIGURACIÓN:")
            for error in errors:
                print(f"   {error}")
            print("\n💡 Verifica tu archivo .env\n")
            return False
        
        return True


# Instancia global
settings = Settings()