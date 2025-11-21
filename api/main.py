"""
API FastAPI con Memoria + Sistema de Feedback + Recommendations (V5)
✅ Orchestrator V5 (4 agentes)
✅ Contexto conversacional ✅
✅ Endpoints para guardar/listar feedback
✅ Vinculación con thread_id
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
from typing import Optional, Dict, Any, List

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "meta-ads-agent"
os.environ["LANGSMITH_TRACING"] = "true"

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# ESTADO GLOBAL
# ============================================
AGENT_READY = False
orchestrator_v5 = None

# 🆕 ALMACENAMIENTO EN MEMORIA PARA FEEDBACK
FEEDBACK_STORAGE: List[Dict[str, Any]] = []

# 🆕 ALMACENAMIENTO DE HISTORIAL DE MENSAJES POR THREAD
THREAD_MESSAGES: Dict[str, List[BaseMessage]] = {}


# ============================================
# SCHEMAS
# ============================================
class QueryRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None
    user_id: str = "default"


class QueryResponse(BaseModel):
    response: str
    thread_id: str
    workflow_type: str
    metadata: Dict[str, Any] = {}
    timestamp: str


class FeedbackRequest(BaseModel):
    thread_id: str
    message_index: int
    rating: int
    comment: Optional[str] = None
    evaluator: Optional[str] = "user"
    agent_id: Optional[str] = "meta-ads-agent"


class FeedbackResponse(BaseModel):
    id: str
    thread_id: str
    message_index: int
    rating: int
    comment: Optional[str]
    evaluator: str
    agent_id: str
    status: str
    created_at: str


class UpdateFeedbackRequest(BaseModel):
    status: str


# ============================================
# FUNCIONES AUXILIARES PARA CONTEXTO
# ============================================

def get_thread_messages(thread_id: str) -> List[BaseMessage]:
    """Obtiene el historial de mensajes de un thread"""
    return THREAD_MESSAGES.get(thread_id, [])


def add_message_to_thread(thread_id: str, message: BaseMessage):
    """Agrega un mensaje al historial del thread"""
    if thread_id not in THREAD_MESSAGES:
        THREAD_MESSAGES[thread_id] = []
    THREAD_MESSAGES[thread_id].append(message)
    
    # Mantener solo últimos 20 mensajes para no saturar memoria
    if len(THREAD_MESSAGES[thread_id]) > 20:
        THREAD_MESSAGES[thread_id] = THREAD_MESSAGES[thread_id][-20:]


def clear_thread_messages(thread_id: str):
    """Limpia el historial de un thread"""
    if thread_id in THREAD_MESSAGES:
        del THREAD_MESSAGES[thread_id]


# ============================================
# INICIALIZACIÓN ASÍNCRONA
# ============================================
async def initialize_agent_background():
    global AGENT_READY, orchestrator_v5
    
    logger.info("⏳ Iniciando carga asíncrona del agente V5...")
    
    try:
        from langgraph_agent.orchestration.orchestrator_v5 import OrchestratorV5
        
        logger.info("📦 Módulos importados")
        
        orchestrator_v5 = OrchestratorV5(enable_logging=True)
        
        AGENT_READY = True
        
        logger.info("✅ Orchestrator V5 completamente inicializado (4 agentes)")
        logger.info("   - ConfigAgent ✅")
        logger.info("   - PerformanceAgent ✅")
        logger.info("   - RecommendationAgent ✅")
        logger.info("   - Multi-Agent ✅")
        logger.info("   - Contexto conversacional ✅")
        
    except Exception as e:
        logger.error(f"❌ Error crítico al inicializar agente: {e}")
        import traceback
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Servidor FastAPI iniciando...")
    asyncio.create_task(initialize_agent_background())
    yield
    logger.info("🛑 Servidor cerrando...")


# ============================================
# APLICACIÓN FASTAPI
# ============================================
api = FastAPI(
    title="Meta Ads Agent API V5",
    description="Agente LangGraph con 4 agentes especializados + Contexto Conversacional + Sistema de Feedback",
    version="5.1-context",
    lifespan=lifespan
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# ENDPOINTS PRINCIPALES
# ============================================
@api.get("/health")
def health_check():
    """Health check que siempre responde rápido"""
    checks = {
        "server": "running",
        "agent_ready": AGENT_READY,
        "orchestrator_v5": orchestrator_v5 is not None,
        "google_api": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
        "meta_api": bool(os.getenv("META_ACCESS_TOKEN")),
        "context_enabled": True,  # ✅ Nuevo
    }
    
    agents_available = 4 if AGENT_READY else 0
    
    status = "healthy" if True else "unhealthy"
    
    return {
        "status": status,
        "checks": checks,
        "version": "5.1-context",
        "agents_available": agents_available,
        "agent_types": [
            "ConfigAgent",
            "PerformanceAgent",
            "RecommendationAgent",
            "Multi-Agent"
        ] if AGENT_READY else [],
        "features": [
            "Conversational Context",  # ✅ Nuevo
            "Thread Memory",
            "Feedback System"
        ],
        "active_threads": len(THREAD_MESSAGES),  # ✅ Nuevo
        "feedback_count": len(FEEDBACK_STORAGE),
        "message": "Servidor operativo con contexto conversacional" if AGENT_READY else "Agente inicializando..."
    }


@api.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Procesar query con el agente V5 + contexto conversacional"""
    if not AGENT_READY or orchestrator_v5 is None:
        raise HTTPException(
            status_code=503, 
            detail="Agente aún inicializando. Por favor espera 30 segundos y reintenta."
        )
    
    try:
        # Generar thread_id si no existe
        if not request.thread_id:
            thread_id = f"thread_{uuid.uuid4().hex[:12]}"
        else:
            thread_id = request.thread_id
        
        logger.info(f"🔥 Query recibida - Thread: {thread_id}")
        logger.info(f"   Query: '{request.query[:100]}...'")
        
        # ✅ OBTENER HISTORIAL DE MENSAJES
        messages = get_thread_messages(thread_id)
        
        if messages:
            logger.info(f"   📚 Usando contexto: {len(messages)} mensajes previos")
        
        # ✅ PROCESAR CON CONTEXTO
        result = orchestrator_v5.process_query(
            query=request.query,
            thread_id=thread_id,
            messages=messages  # ✅ Pasar historial
        )
        
        # ✅ GUARDAR MENSAJES EN EL HISTORIAL
        add_message_to_thread(thread_id, HumanMessage(content=request.query))
        add_message_to_thread(thread_id, AIMessage(content=result.content))
        
        logger.info(f"✅ Query procesada - Thread: {thread_id}")
        logger.info(f"   Workflow: {result.workflow_type}")
        logger.info(f"   Mensajes en thread: {len(THREAD_MESSAGES.get(thread_id, []))}")
        
        return QueryResponse(
            response=result.content,
            thread_id=thread_id,
            workflow_type=result.workflow_type,
            metadata=result.metadata or {},
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"❌ Error procesando query: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================
# 🆕 ENDPOINTS DE FEEDBACK
# ============================================

@api.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """Guardar feedback de un mensaje específico"""
    try:
        feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
        
        feedback_data = {
            "id": feedback_id,
            "thread_id": feedback.thread_id,
            "message_index": feedback.message_index,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "evaluator": feedback.evaluator,
            "agent_id": feedback.agent_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        FEEDBACK_STORAGE.append(feedback_data)
        
        logger.info(
            f"✅ Feedback guardado - ID: {feedback_id}, "
            f"Thread: {feedback.thread_id}, Rating: {feedback.rating}/10"
        )
        
        return FeedbackResponse(**feedback_data)
    
    except Exception as e:
        logger.error(f"❌ Error guardando feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/feedback")
async def list_feedback(
    thread_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100
):
    """Listar feedback con filtros opcionales"""
    try:
        filtered = FEEDBACK_STORAGE
        
        if thread_id:
            filtered = [f for f in filtered if f["thread_id"] == thread_id]
        
        if agent_id:
            filtered = [f for f in filtered if f["agent_id"] == agent_id]
        
        filtered = sorted(
            filtered,
            key=lambda x: x["created_at"],
            reverse=True
        )[:limit]
        
        if filtered:
            ratings = [f["rating"] for f in filtered]
            avg_rating = sum(ratings) / len(ratings)
            
            promoters = len([r for r in ratings if r >= 9])
            detractors = len([r for r in ratings if r <= 6])
            nps = ((promoters - detractors) / len(ratings)) * 100 if ratings else 0
        else:
            avg_rating = 0
            nps = 0
        
        return {
            "data": filtered,
            "total": len(filtered),
            "stats": {
                "avg_rating": round(avg_rating, 1),
                "nps_score": round(nps, 0),
                "total_feedback": len(FEEDBACK_STORAGE),
                "pending": len([f for f in FEEDBACK_STORAGE if f["status"] == "pending"]),
                "applied": len([f for f in FEEDBACK_STORAGE if f["status"] == "applied"])
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Error listando feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/feedback/{feedback_id}")
async def get_feedback(feedback_id: str):
    """Obtener un feedback específico por ID"""
    feedback = next((f for f in FEEDBACK_STORAGE if f["id"] == feedback_id), None)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")
    
    return feedback


@api.put("/feedback/{feedback_id}")
async def update_feedback(feedback_id: str, update: UpdateFeedbackRequest):
    """Actualizar estado de un feedback"""
    try:
        feedback = next((f for f in FEEDBACK_STORAGE if f["id"] == feedback_id), None)
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback no encontrado")
        
        if update.status not in ["pending", "applied", "dismissed"]:
            raise HTTPException(status_code=400, detail="Estado inválido")
        
        feedback["status"] = update.status
        feedback["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"✅ Feedback {feedback_id} actualizado a: {update.status}")
        
        return feedback
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api.delete("/feedback/{feedback_id}")
async def delete_feedback(feedback_id: str):
    """Eliminar un feedback"""
    global FEEDBACK_STORAGE
    
    feedback = next((f for f in FEEDBACK_STORAGE if f["id"] == feedback_id), None)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")
    
    FEEDBACK_STORAGE = [f for f in FEEDBACK_STORAGE if f["id"] != feedback_id]
    
    logger.info(f"🗑️ Feedback {feedback_id} eliminado")
    
    return {"message": "Feedback eliminado", "id": feedback_id}

# ============================================
# ðŸ†• ENDPOINTS DE MÃ‰TRICAS Y DEBUG
# ============================================

@api.get("/metrics")
async def get_metrics():
    """Obtener mÃ©tricas del orchestrator"""
    if not AGENT_READY or orchestrator_v5 is None:
        raise HTTPException(status_code=503, detail="Agente no inicializado")
    
    try:
        metrics = orchestrator_v5.get_metrics()
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"âŒ Error obteniendo mÃ©tricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/agents")
async def list_agents():
    """Listar agentes disponibles"""
    return {
        "agents": [
            {
                "name": "ConfigAgent",
                "description": "ConfiguraciÃ³n tÃ©cnica de campaÃ±as",
                "capabilities": [
                    "Listar campaÃ±as",
                    "Buscar campaÃ±as por nombre",
                    "Presupuestos",
                    "Estrategias de puja",
                    "Detalles de adsets"
                ]
            },
            {
                "name": "PerformanceAgent",
                "description": "MÃ©tricas de rendimiento",
                "capabilities": [
                    "Gasto real",
                    "Impresiones, clicks, CTR",
                    "CPM, CPC, CPA",
                    "Conversiones",
                    "TOP N anuncios",
                    "Comparaciones de perÃ­odos"
                ]
            },
            {
                "name": "RecommendationAgent",
                "description": "Recomendaciones de optimizaciÃ³n",
                "capabilities": [
                    "Detectar Advantage+ no activado",
                    "Identificar presupuestos bajos",
                    "Analizar targeting subÃ³ptimo",
                    "Sugerencias para reducir CPA/CPC"
                ]
            },
            {
                "name": "Multi-Agent",
                "description": "CombinaciÃ³n de mÃºltiples agentes",
                "capabilities": [
                    "AnÃ¡lisis completo de campaÃ±as",
                    "Reportes con config + rendimiento + recomendaciones"
                ]
            }
        ],
        "total_agents": 4,
        "agent_ready": AGENT_READY
    }


# ============================================
# OTROS ENDPOINTS
# ============================================
@api.post("/reset")
async def reset_conversation():
    """Crear nuevo thread_id para nueva conversaciÃ³n"""
    new_thread_id = f"thread_{uuid.uuid4().hex[:12]}"
    return {"thread_id": new_thread_id, "message": "Nueva conversaciÃ³n"}


@api.get("/")
async def root():
    """Root endpoint con informaciÃ³n del servicio"""
    return {
        "service": "Meta Ads Agent API V5",
        "version": "5.0-recommendations",
        "status": "operational" if AGENT_READY else "initializing",
        "agent_ready": AGENT_READY,
        "agents_count": 4,
        "endpoints": {
            "health": "/health (GET)",
            "query": "/query (POST)",
            "feedback": "/feedback (GET, POST)",
            "feedback_detail": "/feedback/{id} (GET, PUT, DELETE)",
            "metrics": "/metrics (GET)",
            "agents": "/agents (GET)",
            "reset": "/reset (POST)",
            "docs": "/docs",
            "status": "/status (GET)"
        }
    }


@api.get("/status")
async def status():
    """Status detallado del sistema"""
    return {
        "agent_ready": AGENT_READY,
        "orchestrator_v5_initialized": orchestrator_v5 is not None,
        "agents": {
            "config_agent": AGENT_READY,
            "performance_agent": AGENT_READY,
            "recommendation_agent": AGENT_READY,
            "multi_agent": AGENT_READY
        },
        "feedback_system": {
            "enabled": True,
            "total_feedback": len(FEEDBACK_STORAGE),
            "storage": "in-memory"
        },
        "environment": {
            "has_google_api": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
            "has_meta_api": bool(os.getenv("META_ACCESS_TOKEN")),
            "has_langsmith": bool(os.getenv("LANGCHAIN_API_KEY"))
        },
        "version": "5.0-recommendations"
    }

@api.get("/info")
async def get_info():
    """Información del servidor para LangSmith Studio"""
    return {
        "type": "langgraph",
        "version": "5.1-context",
        "name": "Meta Ads Agent API V5"
    }


@api.post("/assistants/search")
async def search_assistants():
    """Buscar assistants disponibles para LangSmith Studio"""
    if not AGENT_READY:
        return {"assistants": []}
    
    return {
        "assistants": [
            {
                "assistant_id": "meta-ads-orchestrator",
                "name": "Meta Ads Orchestrator V5",
                "description": "Agente multi-especialista con 4 agentes (Config, Performance, Recommendation, Multi-Agent)",
                "config": {
                    "configurable": {
                        "thread_id": "default"
                    }
                }
            }
        ]
    }


@api.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str):
    """Obtener detalles de un assistant"""
    if assistant_id != "meta-ads-orchestrator":
        raise HTTPException(status_code=404, detail="Assistant no encontrado")
    
    return {
        "assistant_id": "meta-ads-orchestrator",
        "name": "Meta Ads Orchestrator V5",
        "description": "Agente multi-especialista",
        "created_at": datetime.utcnow().isoformat()
    }


@api.post("/threads")
async def create_thread():
    """Crear un nuevo thread para LangSmith Studio"""
    thread_id = f"thread_{uuid.uuid4().hex[:12]}"
    return {
        "thread_id": thread_id,
        "created_at": datetime.utcnow().isoformat()
    }


@api.post("/threads/{thread_id}/runs")
async def run_assistant(thread_id: str, request: dict):
    """Ejecutar el assistant en un thread"""
    if not AGENT_READY or orchestrator_v5 is None:
        raise HTTPException(status_code=503, detail="Agente inicializando")
    
    try:
        # Obtener query del request
        user_input = request.get("input", {}).get("query", "")
        
        if not user_input:
            raise HTTPException(status_code=400, detail="Query requerida")
        
        # Procesar con tu orchestrator
        messages = get_thread_messages(thread_id)
        result = orchestrator_v5.process_query(
            query=user_input,
            thread_id=thread_id,
            messages=messages
        )
        
        # Guardar en historial
        add_message_to_thread(thread_id, HumanMessage(content=user_input))
        add_message_to_thread(thread_id, AIMessage(content=result.content))
        
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        
        return {
            "run_id": run_id,
            "thread_id": thread_id,
            "status": "success",
            "output": {
                "response": result.content,
                "workflow_type": result.workflow_type,
                "metadata": result.metadata or {}
            },
            "created_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error en run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """Obtener estado del thread"""
    messages = get_thread_messages(thread_id)
    
    return {
        "thread_id": thread_id,
        "values": {
            "messages": [
                {
                    "type": "human" if isinstance(m, HumanMessage) else "ai",
                    "content": m.content
                }
                for m in messages
            ]
        },
        "next": []
    }