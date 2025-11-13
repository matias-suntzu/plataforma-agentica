"""
Configuración centralizada de la aplicación
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuración de la aplicación."""
    
    # Meta Ads API
    META_APP_ID = os.getenv("META_APP_ID")
    META_APP_SECRET = os.getenv("META_APP_SECRET")
    META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
    AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID", "act_952835605437684")
    
    # Google/Gemini
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # LangSmith
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "meta-ads-agent")
    
    # Integraciones opcionales
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
    
    # Validar configuración crítica
    @classmethod
    def validate(cls):
        """Valida que las variables críticas estén configuradas."""
        errors = []
        
        if not cls.META_ACCESS_TOKEN:
            errors.append("META_ACCESS_TOKEN no configurado")
        
        if not cls.AD_ACCOUNT_ID:
            errors.append("AD_ACCOUNT_ID no configurado")
        
        if not cls.GOOGLE_API_KEY and not cls.GEMINI_API_KEY:
            errors.append("GOOGLE_API_KEY o GEMINI_API_KEY no configurado")
        
        if errors:
            error_msg = "\n".join([f"  - {e}" for e in errors])
            raise ValueError(f"❌ Configuración inválida:\n{error_msg}")
        
        return True


# Instancia singleton
settings = Settings()

# Validar al importar (solo en producción)
if os.getenv("SKIP_VALIDATION") != "true":
    try:
        settings.validate()
        print("✅ Configuración validada correctamente")
    except ValueError as e:
        print(str(e))
        # No lanzar error en desarrollo, solo advertir
        if os.getenv("ENV") == "production":
            raise