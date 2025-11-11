#!/usr/bin/env python3
"""
Script de Reorganización Automática - langgraph_agent/
Convierte estructura monolítica en modular

BACKUP AUTOMÁTICO: Crea langgraph_agent_backup/ antes de modificar

Ejecutar desde la raíz del proyecto:
    python reorganize_langgraph.py
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def print_header(text):
    print("\n" + "=" * 70)
    print(f"🔧 {text}")
    print("=" * 70)

def create_backup(source_dir):
    """Crea backup de la carpeta original"""
    backup_name = f"{source_dir.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = source_dir.parent / backup_name
    
    print(f"\n💾 Creando backup...")
    shutil.copytree(source_dir, backup_path)
    print(f"   ✅ Backup creado: {backup_name}/")
    return backup_path

def create_directory_structure(base_dir):
    """Crea la estructura de carpetas modular"""
    print("\n📁 Creando estructura de carpetas...")
    
    folders = [
        "core",
        "workflows",
        "orchestration",
        "safety",
        "memory",
        "utils",
        "api",
    ]
    
    for folder in folders:
        folder_path = base_dir / folder
        folder_path.mkdir(exist_ok=True)
        print(f"   ✅ Creada: {folder}/")
    
    return folders

def create_init_files(base_dir, folders):
    """Crea archivos __init__.py en todas las carpetas"""
    print("\n📝 Creando archivos __init__.py...")
    
    init_contents = {
        "core": '''"""Core del agente LangGraph"""
from .agent import app

__all__ = ['app']
''',
        "workflows": '''"""Workflows del agente"""
from .base import WorkflowResult, FastPathWorkflow, AgenticWorkflow

__all__ = ['WorkflowResult', 'FastPathWorkflow', 'AgenticWorkflow']
''',
        "orchestration": '''"""Orquestación y routing"""
from .orchestrator import OrchestratorV3
from .router import QueryRouterV3

__all__ = ['OrchestratorV3', 'QueryRouterV3']
''',
        "safety": '''"""Sistemas de seguridad"""
from .guardrails import GuardrailsManager
from .anomaly_detector import AnomalyDetector

__all__ = ['GuardrailsManager', 'AnomalyDetector']
''',
        "memory": '''"""Memoria y conocimiento"""
from .rag_manager import RAGManager
from .memory_manager import MemoryManager
from .caching import CacheManager

__all__ = ['RAGManager', 'MemoryManager', 'CacheManager']
''',
        "utils": '''"""Utilidades"""
# Funciones auxiliares

__all__ = []
''',
        "api": '''"""API FastAPI para Render"""
from .main import api

__all__ = ['api']
''',
    }
    
    for folder, content in init_contents.items():
        init_path = base_dir / folder / "__init__.py"
        init_path.write_text(content, encoding='utf-8')
        print(f"   ✅ {folder}/__init__.py")

def move_files(base_dir):
    """Mueve archivos a sus nuevas ubicaciones"""
    print("\n📦 Moviendo archivos...")
    
    # Mapeo: archivo_origen -> carpeta_destino
    file_mapping = {
        # Core
        "agent.py": "core",
        
        # Workflows
        "workflows_v2.py": "workflows",  # Se renombrará después
        
        # Orchestration
        "router_v2.py": "orchestration",
        "orchestrator_v3.py": "orchestration",
        
        # Safety
        "guardrails.py": "safety",
        "anomaly_detector.py": "safety",
        
        # Memory
        "rag_manager.py": "memory",
        "memory_manager.py": "memory",
        "caching_system.py": "memory",
    }
    
    moved = []
    not_found = []
    
    for file, dest_folder in file_mapping.items():
        source = base_dir / file
        dest_dir = base_dir / dest_folder
        
        if source.exists():
            dest = dest_dir / file
            shutil.move(str(source), str(dest))
            moved.append((file, dest_folder))
            print(f"   ✅ {file} → {dest_folder}/")
        else:
            not_found.append(file)
            print(f"   ⚠️  No encontrado: {file}")
    
    return moved, not_found

def rename_files(base_dir):
    """Renombra archivos para consistencia"""
    print("\n✏️  Renombrando archivos...")
    
    renames = [
        ("orchestration/router_v2.py", "orchestration/router.py"),
        ("orchestration/orchestrator_v3.py", "orchestration/orchestrator.py"),
        ("memory/caching_system.py", "memory/caching.py"),
    ]
    
    for old_name, new_name in renames:
        old_path = base_dir / old_name
        new_path = base_dir / new_name
        
        if old_path.exists():
            old_path.rename(new_path)
            print(f"   ✅ {old_name} → {new_name}")
        else:
            print(f"   ⚠️  No encontrado: {old_name}")

def split_workflows(base_dir):
    """Divide workflows_v2.py en archivos separados"""
    print("\n✂️  Dividiendo workflows...")
    
    workflows_file = base_dir / "workflows" / "workflows_v2.py"
    
    if not workflows_file.exists():
        print("   ⚠️  workflows_v2.py no encontrado, saltando división")
        return
    
    # Leer contenido
    content = workflows_file.read_text(encoding='utf-8')
    
    # Crear base.py con WorkflowResult y clases base
    base_content = '''"""
Workflows base: WorkflowResult, FastPath, Agentic
"""
import requests
from typing import Dict, Any
from datetime import datetime

class WorkflowResult:
    """Resultado estandarizado"""
    def __init__(self, content: str, workflow_type: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.workflow_type = workflow_type
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "content": self.content,
            "workflow_type": self.workflow_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

# TODO: Copiar manualmente FastPathWorkflow y AgenticWorkflow desde workflows_v2.py
'''
    
    base_file = base_dir / "workflows" / "base.py"
    base_file.write_text(base_content, encoding='utf-8')
    print("   ✅ workflows/base.py creado")
    
    # Crear archivos vacíos para los demás workflows
    workflow_files = [
        "sequential.py",
        "conversation.py",
        "autonomous.py",
        "period_comparison.py"
    ]
    
    for wf_file in workflow_files:
        wf_path = base_dir / "workflows" / wf_file
        wf_path.write_text(f'"""TODO: Extraer de workflows_v2.py"""\n', encoding='utf-8')
        print(f"   ✅ workflows/{wf_file} creado (vacío)")
    
    print("\n   ⚠️  ACCIÓN MANUAL REQUERIDA:")
    print("      Debes copiar manualmente las clases de workflows_v2.py a:")
    print("      - base.py (FastPathWorkflow, AgenticWorkflow)")
    print("      - sequential.py (SequentialWorkflow)")
    print("      - conversation.py (ConversationWorkflow)")
    print("      - autonomous.py (AutonomousOptimizationWorkflow)")

def create_api_files(base_dir):
    """Crea archivos de la API para Render"""
    print("\n🌐 Creando API para Render...")
    
    main_py = base_dir / "api" / "main.py"
    main_content = '''"""
FastAPI App - Entry point para Render
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

# TODO: Ajustar imports después de completar reorganización
# from ..core.agent import app as agent_app
# from ..orchestration.orchestrator import OrchestratorV3

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
    return {"status": "online", "service": "Meta Ads Agent"}

@api.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected" if os.getenv("DATABASE_URL") else "not configured"
    }

@api.post("/query", response_model=QueryResponse)
def process_query(request: QueryRequest):
    """TODO: Implementar después de reorganización"""
    raise HTTPException(status_code=501, detail="Implementación pendiente")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(api, host="0.0.0.0", port=port)
'''
    
    main_py.write_text(main_content, encoding='utf-8')
    print("   ✅ api/main.py creado")

def create_config_files(base_dir):
    """Crea archivos de configuración"""
    print("\n⚙️  Creando archivos de configuración...")
    
    # requirements.txt
    requirements = base_dir / "requirements.txt"
    req_content = '''# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0

# LangChain & LangGraph
langchain==0.1.0
langchain-google-genai==1.0.0
langgraph==0.0.40
langchain-chroma==0.1.0
langchain-community==0.0.19

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# Utilities
requests==2.31.0
pydantic==2.5.0
'''
    requirements.write_text(req_content, encoding='utf-8')
    print("   ✅ requirements.txt")
    
    # .env.example
    env_example = base_dir / ".env.example"
    env_content = '''# API Keys
GEMINI_API_KEY=your_gemini_key_here
LANGCHAIN_API_KEY=your_langsmith_key_here

# Tool Server
TOOL_SERVER_BASE_URL=http://localhost:8000
TOOL_API_KEY=your_tool_api_key

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=meta-ads-agent-dev

# Database (Render provides this automatically)
DATABASE_URL=postgresql://user:pass@host:port/db
'''
    env_example.write_text(env_content, encoding='utf-8')
    print("   ✅ .env.example")
    
    # __init__.py raíz
    root_init = base_dir / "__init__.py"
    init_content = '''"""
Meta Ads Agent - LangGraph
"""
from .core.agent import app
from .orchestration.orchestrator import OrchestratorV3

__version__ = "1.0.0"
__all__ = ["app", "OrchestratorV3"]
'''
    root_init.write_text(init_content, encoding='utf-8')
    print("   ✅ __init__.py (raíz)")

def create_migration_guide(base_dir, backup_path):
    """Crea guía de migración manual"""
    print("\n📖 Creando guía de migración...")
    
    guide = base_dir / "MIGRATION_GUIDE.md"
    guide_content = f'''# 📋 Guía de Migración Manual

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
`{backup_path.name}/`

Si algo sale mal, puedes restaurar:
```bash
rm -rf langgraph_agent/
mv {backup_path.name}/ langgraph_agent/
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

**Fecha de migración:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
'''
    
    guide.write_text(guide_content, encoding='utf-8')
    print(f"   ✅ MIGRATION_GUIDE.md creado")

def print_summary(moved, not_found):
    """Imprime resumen de la reorganización"""
    print_header("RESUMEN DE REORGANIZACIÓN")
    
    print(f"\n✅ Archivos movidos exitosamente: {len(moved)}")
    for file, folder in moved:
        print(f"   - {file} → {folder}/")
    
    if not_found:
        print(f"\n⚠️  Archivos no encontrados: {len(not_found)}")
        for file in not_found:
            print(f"   - {file}")
        print("\n   Estos archivos pueden no existir en tu proyecto actual.")
        print("   Revisa MIGRATION_GUIDE.md para más detalles.")
    
    print("\n📁 Estructura final:")
    print("""
    📁 langgraph_agent/
      ├── 📁 core/              ✅
      ├── 📁 workflows/         ✅
      ├── 📁 orchestration/     ✅
      ├── 📁 safety/            ✅
      ├── 📁 memory/            ✅
      ├── 📁 utils/             ✅
      ├── 📁 api/               ✅
      ├── __init__.py           ✅
      ├── requirements.txt      ✅
      └── .env.example          ✅
    """)
    
    print("\n⚠️  ACCIONES MANUALES REQUERIDAS:")
    print("   1. Dividir workflows_v2.py en archivos separados")
    print("   2. Actualizar imports en todos los archivos")
    print("   3. Completar api/main.py con la lógica del orchestrator")
    print("   4. Actualizar core/agent.py para usar PostgreSQL")
    print("   5. Ejecutar tests locales")
    
    print("\n📖 Consulta MIGRATION_GUIDE.md para instrucciones detalladas")

def main():
    print_header("REORGANIZACIÓN AUTOMÁTICA - langgraph_agent/")
    
    # Verificar que estamos en la raíz correcta
    if not Path("langgraph_agent").exists():
        print("\n❌ Error: No se encuentra langgraph_agent/")
        print("   Ejecuta este script desde la raíz del proyecto")
        print(f"   Directorio actual: {Path.cwd()}")
        return
    
    base_dir = Path("langgraph_agent")
    print(f"\n📂 Directorio de trabajo: {base_dir}")
    
    # Confirmación
    print("\n⚠️  ADVERTENCIA: Este script modificará la estructura del proyecto")
    response = input("   ¿Continuar? Se creará un backup automático (s/N): ")
    
    if response.lower() != 's':
        print("❌ Cancelado por el usuario")
        return
    
    try:
        # PASO 1: Backup
        backup_path = create_backup(base_dir)
        
        # PASO 2: Crear estructura
        folders = create_directory_structure(base_dir)
        
        # PASO 3: Crear __init__.py
        create_init_files(base_dir, folders)
        
        # PASO 4: Mover archivos
        moved, not_found = move_files(base_dir)
        
        # PASO 5: Renombrar archivos
        rename_files(base_dir)
        
        # PASO 6: Dividir workflows (parcial)
        split_workflows(base_dir)
        
        # PASO 7: Crear API
        create_api_files(base_dir)
        
        # PASO 8: Crear configs
        create_config_files(base_dir)
        
        # PASO 9: Guía de migración
        create_migration_guide(base_dir, backup_path)
        
        # PASO 10: Resumen
        print_summary(moved, not_found)
        
        print("\n" + "=" * 70)
        print("✅ REORGANIZACIÓN COMPLETADA")
        print("=" * 70)
        print(f"\n💾 Backup guardado en: {backup_path.name}/")
        print("📖 Lee MIGRATION_GUIDE.md para completar la migración")
        print("\n🚀 Siguiente paso: Editar archivos según MIGRATION_GUIDE.md")
        
    except Exception as e:
        print(f"\n❌ ERROR durante la reorganización: {e}")
        print("\n🔄 El backup está disponible en caso de problemas")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()