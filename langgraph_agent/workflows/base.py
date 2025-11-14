"""
Workflows con memoria conversacional
CRÍTICO: Usar RunnableConfig con thread_id
"""

from typing import Dict, Any
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig  # ← IMPORTANTE


class WorkflowResult(BaseModel):
    """Resultado de un workflow"""
    content: str
    workflow_type: str
    metadata: Dict[str, Any] = {}


# ============================================
# FAST PATH (sin memoria - queries simples)
# ============================================
class FastPathWorkflow:
    """Workflow para queries simples sin usar el agente"""
    
    def __init__(self):
        print("⚡ FastPath inicializado (sin memoria)")
    
    def execute(self, query: str) -> WorkflowResult:
        """
        Ejecuta query simple SIN memoria.
        No necesita thread_id porque no usa el agente.
        """
        from ..tools.campaigns import listar_campanas_func
        from ..models.schemas import ListarCampanasInput
        import json
        
        query_lower = query.lower()
        
        # Listar campañas
        if any(kw in query_lower for kw in ["lista", "listar", "campañas"]):
            try:
                result = listar_campanas_func(ListarCampanasInput())
                campanas = json.loads(result.campanas_json)
                
                if "error" in campanas:
                    return WorkflowResult(
                        content=f"❌ Error: {campanas['error']}",
                        workflow_type="simple"
                    )
                
                response = "📋 **Campañas activas:**\n\n"
                for camp in campanas[:10]:
                    response += f"- **{camp['name']}** (ID: `{camp['id']}`)\n"
                
                return WorkflowResult(
                    content=response,
                    workflow_type="simple"
                )
            except Exception as e:
                return WorkflowResult(
                    content=f"❌ Error: {str(e)}",
                    workflow_type="simple"
                )
        
        # Query no reconocida
        return WorkflowResult(
            content="⚠️ Query no reconocida para FastPath. Usar workflow agéntico.",
            workflow_type="simple",
            metadata={"fallback": True}
        )


# ============================================
# AGENTIC WORKFLOW (CON MEMORIA)
# ============================================
class AgenticWorkflow:
    """
    Workflow agéntico con memoria conversacional.
    ✅ USA RunnableConfig con thread_id
    """
    
    def __init__(self, agent_app):
        self.agent_app = agent_app
        print("🤖 AgenticWorkflow inicializado (con memoria)")
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """
        Ejecuta query con el agente LangGraph.
        
        ✅ CRÍTICO: Usar RunnableConfig con thread_id para memoria
        """
        print(f"🤖 AGENTIC WORKFLOW")
        print(f"   Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        
        try:
            # ✅ IMPORTANTE: Configurar con thread_id
            config = RunnableConfig(
                configurable={"thread_id": thread_id}  # ← Esto activa el checkpointing
            )
            
            input_message = HumanMessage(content=query)
            
            # ✅ Invocar con config
            result = self.agent_app.invoke(
                {"messages": [input_message]},
                config=config  # ← Pasar config con thread_id
            )
            
            # Extraer respuesta
            final_message = result["messages"][-1]
            
            if isinstance(final_message.content, str):
                content = final_message.content
            elif isinstance(final_message.content, list):
                content = "\n".join([str(item) for item in final_message.content])
            else:
                content = str(final_message.content)
            
            return WorkflowResult(
                content=content,
                workflow_type="agentic",
                metadata={"thread_id": thread_id}
            )
        
        except Exception as e:
            print(f"   ❌ Error en workflow agéntico: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return WorkflowResult(
                content=f"❌ Error en agente: {str(e)}",
                workflow_type="agentic",
                metadata={"error": str(e), "thread_id": thread_id}
            )