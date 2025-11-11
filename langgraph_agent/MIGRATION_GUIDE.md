# 📋 Guía de Migración Manual

## ✅ Pasos Completados Automáticamente

1. ✅ Estructura de carpetas creada
2. ✅ Archivos movidos a nuevas ubicaciones
3. ✅ Archivos renombrados (router_v2.py → router.py, etc.)
4. ✅ Archivos __init__.py creados
5. ✅ API base creada (api/main.py)
6. ✅ Archivos de configuración creados

## ⚠️ Tareas Pendientes (MANUAL)

### 1. Dividir workflows_v2.py

El archivo `workflows/workflows_v2.py` contiene todas las clases de workflows.
Debes extraer manualmente:

```python
# De workflows_v2.py extraer a:
# - workflows/base.py: WorkflowResult, FastPathWorkflow, AgenticWorkflow
# - workflows/sequential.py: SequentialWorkflow
# - workflows/conversation.py: ConversationWorkflow
# - workflows/autonomous.py: AutonomousOptimizationWorkflow
```

**Proceso:**
1. Abre `workflows/workflows_v2.py`
2. Copia clase `WorkflowResult` → `workflows/base.py`
3. Copia clase `FastPathWorkflow` → `workflows/base.py`
4. Copia clase `AgenticWorkflow` → `workflows/base.py`
5. Copia clase `SequentialWorkflow` → `workflows/sequential.py`
6. Copia clase `ConversationWorkflow` → `workflows/conversation.py`
7. Copia clase `AutonomousOptimizationWorkflow` → `workflows/autonomous.py`
8. Elimina `workflows/workflows_v2.py` cuando termines

### 2. Actualizar imports en archivos

**Archivos que necesitan actualización de imports:**

#### `core/agent.py`
```python
# ANTES:
from rag_manager import RAGManager
from memory_manager import MemoryManager

# DESPUÉS:
from ..memory.rag_manager import RAGManager
from ..memory.memory_manager import MemoryManager
```

#### `orchestration/orchestrator.py`
```python
# ANTES:
from .router_v2 import QueryRouterV2
from .workflows_v2 import FastPathWorkflow, AgenticWorkflow

# DESPUÉS:
from .router import QueryRouterV3
from ..workflows.base import FastPathWorkflow, AgenticWorkflow
from ..workflows.sequential import SequentialWorkflow
from ..workflows.conversation import ConversationWorkflow
from ..workflows.autonomous import AutonomousOptimizationWorkflow
```

#### `orchestration/router.py`
```python
# Sin cambios necesarios (imports solo de stdlib)
```

#### `safety/guardrails.py`
```python
# Sin cambios necesarios
```

#### `safety/anomaly_detector.py`
```python
# Sin cambios necesarios
```

#### `memory/rag_manager.py`
```python
# Actualizar si importa de otros módulos
```

### 3. Completar api/main.py

```python
# Descomentar y ajustar:
from ..core.agent import app as agent_app
from ..orchestration.orchestrator import OrchestratorV3

# Inicializar orchestrator
orchestrator = OrchestratorV3()

# Implementar endpoint /query
@api.post("/query", response_model=QueryResponse)
def process_query(request: QueryRequest):
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
```

### 4. Actualizar core/agent.py para PostgreSQL

```python
# Reemplazar SQLite Checkpointer por PostgreSQL

# ANTES:
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver(conn)

# DESPUÉS:
from langgraph.checkpoint.postgres import PostgresSaver

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
    app = workflow.compile(checkpointer=checkpointer)
else:
    app = workflow.compile()
```

### 5. Testing

```bash
# 1. Instalar dependencias
cd langgraph_agent/
pip install -r requirements.txt

# 2. Configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# 3. Test imports
python -c "from core.agent import app; print('✅ Agent importado')"
python -c "from orchestration.orchestrator import OrchestratorV3; print('✅ Orchestrator importado')"

# 4. Test API local
python -m api.main

# 5. Test endpoint
curl http://localhost:8080/health
```

## 📦 Backup

Tu código original está en:
`langgraph_agent_backup_20251108_023051/`

Si algo sale mal, puedes restaurar:
```bash
rm -rf langgraph_agent/
mv langgraph_agent_backup_20251108_023051/ langgraph_agent/
```

## 🚀 Siguiente: Deploy en Render

Una vez completados los pasos manuales:

1. Commit y push a GitHub
```bash
git add .
git commit -m "refactor: estructura modular para Render"
git push origin main
```

2. Crear servicio en Render (ver docs/DEPLOYMENT_RENDER.md)

## 📚 Recursos

- Documentación LangGraph: https://python.langchain.com/docs/langgraph
- Render Docs: https://render.com/docs
- PostgreSQL Checkpointer: https://python.langchain.com/docs/langgraph/how-tos/persistence-postgres

---

**Fecha de migración:** 2025-11-08 02:32:39
