"""
FastAPI App - Entry point para Render
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports del agente
try:
    from ..core.agent import app as agent_app
    from ..orchestration.orchestrator import OrchestratorV3
    
    orchestrator = OrchestratorV3()
    logger.info("✅ Orchestrator inicializado correctamente")
except Exception as e:
    logger.error(f"❌ Error inicializando orchestrator: {e}")
    orchestrator = None

api = FastAPI(
    title="Meta Ads Agent API",
    description="Agente LangGraph para Meta Ads",
    version="1.0.0"
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None
    user_id: str = "default"

class QueryResponse(BaseModel):
    content: str
    workflow_type: str
    metadata: dict
    timestamp: str

@api.get("/")
def root():
    return {
        "status": "online", 
        "service": "Meta Ads Agent",
        "orchestrator": "initialized" if orchestrator else "error"
    }

@api.get("/health")
def health_check():
    health_status = {
        "status": "healthy" if orchestrator else "degraded",
        "database": "configured" if os.getenv("DATABASE_URL") else "not configured",
        "google_api": "configured" if os.getenv("GOOGLE_API_KEY") else "missing",
        "orchestrator": "ready" if orchestrator else "error"
    }
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return health_status

@api.post("/query", response_model=QueryResponse)
def process_query(request: QueryRequest):
    if not orchestrator:
        raise HTTPException(
            status_code=503, 
            detail="Orchestrator not initialized. Check server logs."
        )
    
    try:
        result = orchestrator.process_query(
            query=request.query,
            thread_id=request.thread_id,
            user_id=request.user_id
        )
        return QueryResponse(
            content=result.content,
            workflow_type=result.workflow_type,
            metadata=result.metadata,
            timestamp=result.timestamp
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(api, host="0.0.0.0", port=port)