"""
Servidor de Herramientas para Agente de Meta Ads
Versión: 3.2 (Refactorizado y Modular)

Arquitectura:
- config/: Configuración y variables de entorno
- middleware/: Autenticación y seguridad
- models/: Esquemas Pydantic
- tools/: Lógica de negocio de cada herramienta
- utils/: Funciones auxiliares reutilizables
"""

import logging
from fastapi import FastAPI
from langchain_core.runnables import RunnableLambda
from langserve import add_routes

# Configuración
from config.settings import settings
from middleware.auth import AuthMiddleware
from utils.meta_api import init_meta_api

# Modelos
from models.schemas import (
    ListarCampanasInput, BuscarIdCampanaInput,
    ObtenerAnunciosPorRendimientoInput, GetAllCampaignsMetricsInput,
    GetCampaignRecommendationsInput, GetCampaignDetailsInput,
    UpdateAdsetBudgetInput, GenerarReporteGoogleSlidesInput,
    EnviarAlertaSlackInput
)

# Herramientas
from tools.campaigns import listar_campanas_func, buscar_id_campana_func
from tools.ads import obtener_anuncios_por_rendimiento_func
from tools.metrics import get_all_campaigns_metrics_func
from tools.recommendations import (
    get_campaign_recommendations_func,
    get_campaign_details_func
)
from tools.actions import update_adset_budget_func
from tools.integrations import (
    generar_reporte_google_slides_func,
    enviar_alerta_slack_func
)

# ========== LOGGING ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== VALIDAR CONFIGURACIÓN ==========
if not settings.validate():
    logger.error("⚠️ Configuración incompleta. El servidor puede no funcionar correctamente.")

# ========== INICIALIZAR META API ==========
init_meta_api()

# ========== FASTAPI ==========
app = FastAPI(
    title="Servidor de Herramientas Meta Ads",
    version="3.2",
    description="Servidor LangServe modularizado para agente de Meta Ads"
)

# Middleware de autenticación
app.add_middleware(AuthMiddleware)

# ========== DEFINIR CHAINS ==========
chains = {
    '/listarcampanas': RunnableLambda(listar_campanas_func).with_types(
        input_type=ListarCampanasInput
    ),
    '/buscaridcampana': RunnableLambda(buscar_id_campana_func).with_types(
        input_type=BuscarIdCampanaInput
    ),
    '/obteneranunciosrendimiento': RunnableLambda(obtener_anuncios_por_rendimiento_func).with_types(
        input_type=ObtenerAnunciosPorRendimientoInput
    ),
    '/getallcampaignsmetrics': RunnableLambda(get_all_campaigns_metrics_func).with_types(
        input_type=GetAllCampaignsMetricsInput
    ),
    '/getcampaignrecommendations': RunnableLambda(get_campaign_recommendations_func).with_types(
        input_type=GetCampaignRecommendationsInput
    ),
    '/getcampaigndetails': RunnableLambda(get_campaign_details_func).with_types(
        input_type=GetCampaignDetailsInput
    ),
    '/updateadsetbudget': RunnableLambda(update_adset_budget_func).with_types(
        input_type=UpdateAdsetBudgetInput
    ),
    '/generar_reporte_slides': RunnableLambda(generar_reporte_google_slides_func).with_types(
        input_type=GenerarReporteGoogleSlidesInput
    ),
    '/enviaralertaslack': RunnableLambda(enviar_alerta_slack_func).with_types(
        input_type=EnviarAlertaSlackInput
    ),
}

# ========== REGISTRAR RUTAS ==========
for path, chain in chains.items():
    add_routes(app, chain, path=path)

logger.info(f"✅ Servidor inicializado con {len(chains)} herramientas")
logger.info(f"📍 Cuenta Meta Ads: {settings.AD_ACCOUNT_ID}")
logger.info(f"🔐 Autenticación: X-Tool-Api-Key requerido")
logger.info(f"📖 Documentación: http://localhost:8000/docs")

# ========== MAIN ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)