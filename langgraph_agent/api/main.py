"""
FastAPI App - Entry point para Render
Versión con Health Check Inteligente y carga asíncrona
"""

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# ESTADO GLOBAL DEL AGENTE
# ============================================
AGENT_READY = False
AGENT_WORKFLOW = None
orchestrator = None

# ============================================
# FUNCIÓN DE INICIALIZACIÓN ASÍNCRONA
# ============================================
async def initialize_agent_background():
    """
    Inicializa el agente en segundo plano.
    Permite que el servidor responda rápido mientras carga.
    """
    global AGENT_READY, AGENT_WORKFLOW, orchestrator
    
    logger.info("⏳ Iniciando carga asíncrona del agente...")
    
    try:
        # Importar aquí para evitar bloquear el inicio del servidor
        from ..core.agent import app as agent_app
        from ..orchestration.orchestrator import OrchestratorV3
        
        logger.info("📦 Módulos importados")
        
        # Inicializar orchestrator (esto incluye RAG, Memory, etc.)
        logger.info("🚀 Inicializando Orchestrator...")
        orchestrator = OrchestratorV3(
            enable_guardrails=False,
            enable_caching=True,
            enable_anomaly_detection=False
        )
        
        logger.info("🤖 Orchestrator inicializado")
        
        # Guardar el workflow de LangGraph
        AGENT_WORKFLOW = agent_app
        
        # Marcar como listo
        AGENT_READY = True
        
        logger.info("✅ Agente completamente inicializado y listo para tráfico")
        
    except Exception as e:
        logger.error(f"❌ Error crítico durante inicialización: {e}")
        import traceback
        traceback.print_exc()
        # AGENT_READY permanece False


# ============================================
# CICLO DE VIDA DE FASTAPI
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    - Startup: Inicia carga del agente en background
    - Shutdown: Limpieza si es necesario
    """
    # STARTUP
    logger.info("🚀 Servidor FastAPI iniciando...")
    
    # Crear tarea en background (NO usar await aquí)
    asyncio.create_task(initialize_agent_background())
    
    logger.info("✅ Servidor listo. Agente cargando en background...")
    
    # El código después del yield se ejecuta al cerrar
    yield
    
    # SHUTDOWN
    logger.info("🛑 Servidor cerrando...")


# ============================================
# APLICACIÓN FASTAPI
# ============================================
api = FastAPI(
    title="Meta Ads Agent API",
    description="Agente LangGraph con LangSmith para Meta Ads",
    version="3.3-async",
    lifespan=lifespan
)

# CORS
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# SCHEMAS
# ============================================
class QueryRequest(BaseModel):
    query: str
    thread_id: str = None
    user_id: str = "default"


class QueryResponse(BaseModel):
    response: str
    thread_id: str
    workflow_type: str


# ============================================
# HEALTH CHECK INTELIGENTE
# ============================================
@api.get("/health")
async def health_check():
    """
    Health check que responde instantáneamente.
    
    - 503: Agente aún inicializando (Render sigue intentando)
    - 200: Agente listo para recibir tráfico
    """
    if not AGENT_READY:
        logger.warning("⚠️ Health check: Agente aún cargando (503)")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "initializing",
                "message": "Agente LangGraph inicializando. Esto puede tardar 1-2 minutos."
            }
        )
    
    return {
        "status": "ok",
        "agent_ready": True,
        "orchestrator": orchestrator is not None,
        "workflow": AGENT_WORKFLOW is not None
    }


# ============================================
# ENDPOINT PRINCIPAL: QUERY
# ============================================
@api.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Procesa una consulta del usuario.
    
    Requiere que el agente esté completamente inicializado.
    """
    global orchestrator
    
    # Verificar que el agente esté listo
    if not AGENT_READY or orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "initializing",
                "message": "El agente aún no ha terminado de inicializarse. Por favor, espera unos segundos."
            }
        )
    
    try:
        # Procesar la consulta con el orchestrator
        result = orchestrator.process_query(
            query=request.query,
            thread_id=request.thread_id,
            user_id=request.user_id
        )
        
        return QueryResponse(
            response=result.content,
            thread_id=request.thread_id or "default",
            workflow_type=result.workflow_type
        )
    
    except Exception as e:
        logger.error(f"❌ Error procesando query: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando consulta: {str(e)}"
        )


# ============================================
# ENDPOINTS ADICIONALES
# ============================================
@api.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "service": "Meta Ads Agent API",
        "version": "3.3-async",
        "status": "operational" if AGENT_READY else "initializing",
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)",
            "docs": "/docs"
        }
    }


@api.get("/status")
async def status():
    """Endpoint de estado detallado"""
    return {
        "agent_ready": AGENT_READY,
        "orchestrator_initialized": orchestrator is not None,
        "workflow_loaded": AGENT_WORKFLOW is not None,
        "langsmith_enabled": os.getenv("LANGCHAIN_TRACING_V2") == "true"
    }


# ============================================
# MANEJO DE ERRORES GLOBAL
# ============================================
@api.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Maneja excepciones no capturadas"""
    logger.error(f"❌ Excepción no manejada: {exc}")
    import traceback
    traceback.print_exc()
    
    return {
        "error": str(exc),
        "type": type(exc).__name__,
        "path": request.url.path
    }