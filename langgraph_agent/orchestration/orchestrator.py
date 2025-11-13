"""
Workflows base - VERSIÓN UNIFICADA (sin llamadas HTTP)
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

# ✅ Importar herramientas LOCALES
from ..tools.campaigns import listar_campanas_func
from ..models.schemas import ListarCampanasInput


class WorkflowResult(BaseModel):
    """Resultado de un workflow."""
    content: str
    workflow_type: str
    metadata: Dict[str, Any] = {}
    timestamp: str = datetime.now().isoformat()


class FastPathWorkflow:
    """
    Workflow para queries simples que no requieren LLM.
    Ejecuta herramientas directamente sin razonamiento.
    """
    
    def __init__(self):
        """Ya NO necesita langserve_url ni api_key."""
        pass
    
    def execute(self, query: str) -> WorkflowResult:
        """
        Ejecuta herramientas directamente según la query.
        """
        query_lower = query.lower()
        
        try:
            # Patrón: Lista de campañas
            if "lista" in query_lower and "campaña" in query_lower:
                print("⚡ FastPath: Listar campañas")
                
                # ✅ Llamada LOCAL (sin HTTP)
                result = listar_campanas_func(ListarCampanasInput(limite=20))
                
                return WorkflowResult(
                    content=result.campanas_json,
                    workflow_type="simple",
                    metadata={"tool": "ListarCampanas"}
                )
            
            # Si no hay patrón reconocido, devolver mensaje
            return WorkflowResult(
                content="Query no reconocida para FastPath. Usa workflow agéntico.",
                workflow_type="simple",
                metadata={"error": "no_pattern"}
            )
        
        except Exception as e:
            return WorkflowResult(
                content=f"❌ Error en FastPath: {str(e)}",
                workflow_type="error",
                metadata={"error": str(e)}
            )


class AgenticWorkflow:
    """
    Workflow para queries complejas que requieren razonamiento del LLM.
    """
    
    def __init__(self, agent_app):
        """
        Args:
            agent_app: Aplicación LangGraph compilada
        """
        self.agent = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """
        Ejecuta el agente LangGraph completo con razonamiento.
        """
        from langchain_core.messages import HumanMessage
        from langchain_core.runnables import RunnableConfig
        
        print(f"\n🤖 AGENTIC WORKFLOW")
        print(f"   Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        
        try:
            config = RunnableConfig(configurable={"thread_id": thread_id})
            input_message = HumanMessage(content=query)
            
            # Invocar el agente
            final_state = self.agent.invoke({"messages": [input_message]}, config=config)
            
            # Extraer la respuesta final
            final_message = final_state["messages"][-1]
            
            if isinstance(final_message.content, str):
                response = final_message.content
            elif isinstance(final_message.content, list):
                response = "\n".join([str(item) for item in final_message.content])
            else:
                response = str(final_message.content)
            
            print(f"   ✅ Workflow completado")
            
            return WorkflowResult(
                content=response,
                workflow_type="agentic",
                metadata={
                    "thread_id": thread_id,
                    "message_count": len(final_state["messages"])
                }
            )
        
        except Exception as e:
            print(f"   ❌ Error en workflow agéntico: {e}")
            import traceback
            traceback.print_exc()
            
            return WorkflowResult(
                content=f"❌ Error ejecutando agente: {str(e)}",
                workflow_type="error",
                metadata={"error": str(e), "thread_id": thread_id}
            )