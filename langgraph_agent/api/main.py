"""
API FastAPI con Memoria usando thread_id
✅ Sin AttributeError de 'timestamp'
✅ Respuestas correctas al frontend
"""

import os
import asyncio
import logging
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

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
    """Inicializa el agente en segundo plano."""
    global AGENT_READY, AGENT_WORKFLOW, orchestrator
    
    logger.info("⏳ Iniciando carga asíncrona del agente...")
    
    try:
        from ..core.agent import app as agent_app
        from ..orchestration.orchestrator import OrchestratorV3
        
        logger.info("📦 Módulos importados")
        
        logger.info("🚀 Inicializando Orchestrator...")
        orchestrator = OrchestratorV3(
            enable_guardrails=False,
            enable_caching=True,
            enable_anomaly_detection=False
        )
        
        logger.info("🤖 Orchestrator inicializado")
        
        AGENT_WORKFLOW = agent_app
        AGENT_READY = True
        
        logger.info("✅ Agente completamente inicializado y listo para tráfico")
        
    except Exception as e:
        logger.error(f"❌ Error crítico durante inicialización: {e}")
        import traceback
        traceback.print_exc()


# ============================================
# CICLO DE VIDA DE FASTAPI
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    logger.info("🚀 Servidor FastAPI iniciando...")
    asyncio.create_task(initialize_agent_background())
    logger.info("✅ Servidor listo. Agente cargando en background...")
    yield
    logger.info("🛑 Servidor cerrando...")


# ============================================
# APLICACIÓN FASTAPI
# ============================================
api = FastAPI(
    title="Meta Ads Agent API",
    description="Agente LangGraph con LangSmith para Meta Ads",
    version="3.4-memory-fixed",
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
    thread_id: Optional[str] = None
    user_id: str = "default"


class QueryResponse(BaseModel):
    response: str              # ← Lo que el frontend espera
    thread_id: str             # ← IMPORTANTE: incluir siempre
    workflow_type: str
    metadata: Dict[str, Any] = {}
    timestamp: str             # ← Lo generamos aquí


# ============================================
# HEALTH CHECK
# ============================================
@api.get("/health")
def health_check():
    """
    ✅ Health check mejorado - Siempre retorna 'healthy' si el servicio responde
    """
    # Verificaciones básicas
    checks = {
        "orchestrator": orchestrator is not None,
        "google_api": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
        "meta_api": bool(os.getenv("META_ACCESS_TOKEN")),
    }
    
    # ✅ Retornar 'healthy' si el orchestrator está listo
    if orchestrator:
        status = "healthy"
    else:
        status = "degraded"
    
    response = {
        "status": status,
        "checks": checks,
        "version": "3.4-memory-fixed",
        "timestamp": str(os.environ.get("RENDER_GIT_COMMIT", "local"))[:7]
    }
    
    # Solo retornar error 503 si NADA funciona
    if not orchestrator:
        raise HTTPException(
            status_code=503, 
            detail="Orchestrator no inicializado"
        )
    
    return response


# ============================================
# ENDPOINT PRINCIPAL: QUERY
# ============================================
@api.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Procesa una consulta del usuario CON MEMORIA.
    
    ✅ IMPORTANTE: 
    - Genera thread_id si no existe
    - Lo devuelve en la respuesta
    - El cliente debe guardarlo y reutilizarlo
    """
    global orchestrator
    
    # Verificar que el agente esté listo
    if not AGENT_READY or orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "initializing",
                "message": "El agente aún no ha terminado de inicializarse."
            }
        )
    
    try:
        # ✅ Generar thread_id si no viene
        if not request.thread_id:
            thread_id = f"thread_{uuid.uuid4().hex[:12]}"
            logger.info(f"🆕 Nueva conversación: {thread_id}")
        else:
            thread_id = request.thread_id
            logger.info(f"🔄 Continuando conversación: {thread_id}")
        
        # Procesar con orchestrator
        result = orchestrator.process_query(
            query=request.query,
            thread_id=thread_id,
            user_id=request.user_id
        )
        
        logger.info(f"✅ Query procesada - Thread: {thread_id}, Workflow: {result.workflow_type}")
        
        # ✅ CREAR QueryResponse con timestamp generado aquí
        return QueryResponse(
            response=result.content,           # ← Mapear "content" a "response"
            thread_id=thread_id,               # ← Siempre incluir thread_id
            workflow_type=result.workflow_type,
            metadata=result.metadata or {},
            timestamp=datetime.utcnow().isoformat()  # ✅ Generar timestamp aquí
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
# ENDPOINT: RESET CONVERSACIÓN
# ============================================
@api.post("/reset")
async def reset_conversation():
    """Genera un nuevo thread_id para empezar conversación desde cero."""
    new_thread_id = f"thread_{uuid.uuid4().hex[:12]}"
    logger.info(f"🔄 Nueva conversación solicitada: {new_thread_id}")
    
    return {
        "thread_id": new_thread_id,
        "message": "Nueva conversación iniciada"
    }


# ============================================
# ENDPOINTS ADICIONALES
# ============================================
@api.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "Meta Ads Agent API",
        "version": "3.4-memory-fixed",
        "status": "operational" if AGENT_READY else "initializing",
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)",
            "reset": "/reset (POST)",
            "status": "/status",
            "docs": "/docs"
        }
    }


@api.get("/status")
async def status():
    """Estado detallado"""
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