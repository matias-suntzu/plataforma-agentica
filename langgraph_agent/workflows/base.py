"""
Workflows base: WorkflowResult, FastPath, Agentic
VERSIÓN UNIFICADA - Sin llamadas HTTP
"""
from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage

# ✅ Importar herramientas LOCALES
from ..tools.campaigns import listar_campanas_func
from ..models.schemas import ListarCampanasInput


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


class FastPathWorkflow:
    """Workflow SIMPLE - Respuesta directa sin agente usando herramientas locales."""
    
    def __init__(self):
        """Ya NO necesita langserve_url ni api_key."""
        pass
    
    def execute(self, query: str) -> WorkflowResult:
        """Ejecuta el Fast Path con herramientas locales."""
        print(f"\n⚡ FAST PATH WORKFLOW")
        print(f"   Query: '{query}'")
        
        query_lower = query.lower()
        
        try:
            # Patrón: Lista de campañas
            if "lista" in query_lower and ("campaña" in query_lower or "campana" in query_lower):
                print("   🔧 Ejecutando: ListarCampanas (local)")
                
                # ✅ Llamada LOCAL (sin HTTP)
                result = listar_campanas_func(ListarCampanasInput(limite=20))
                
                content = f"🤖 Llamada directa a herramienta local.\n\n**Resultado:**\n```json\n{result.campanas_json[:2000]}...\n```"
                
                return WorkflowResult(
                    content=content,
                    workflow_type="simple",
                    metadata={"tool_used": "ListarCampanas", "local": True}
                )
            
            # Si no hay patrón reconocido
            return WorkflowResult(
                content="Query no reconocida para FastPath. Usa workflow agéntico.",
                workflow_type="simple",
                metadata={"error": "no_pattern"}
            )
        
        except Exception as e:
            print(f"   ❌ Error en FastPath: {e}")
            return WorkflowResult(
                content=f"❌ Error en FastPath: {str(e)}",
                workflow_type="error",
                metadata={"error": str(e)}
            )


class AgenticWorkflow:
    """Workflow AGENTIC - Usa el agente con LangGraph para razonamiento."""
    
    def __init__(self, agent_app):
        self.agent = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """Ejecuta el workflow agéntico."""
        print(f"\n🤖 AGENTIC WORKFLOW")
        print(f"   Query: '{query}'")
        print(f"   Thread ID: {thread_id}")

        try:
            config = {"configurable": {"thread_id": thread_id}}
            input_message = HumanMessage(content=query)
            
            # Invocar el agente
            final_state = self.agent.invoke({"messages": [input_message]}, config=config)
            
            # Extraer el último mensaje
            final_message = final_state["messages"][-1]

            # Procesar contenido del mensaje
            def extract_text_from_gemini(content):
                """Extrae texto limpio de respuestas de Gemini"""
                if isinstance(content, dict):
                    if "text" in content:
                        return content["text"]
                    elif "content" in content:
                        return str(content["content"])
                    else:
                        # Filtrar 'extras' y convertir a string
                        filtered = {k: v for k, v in content.items() if k != 'extras'}
                        return str(filtered)
                elif isinstance(content, list):
                    texts = []
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            texts.append(item["text"])
                        else:
                            texts.append(str(item))
                    return "\n".join(texts) if texts else "El agente ha finalizado sin respuesta."
                else:
                    return str(content)
            
            content = extract_text_from_gemini(final_message.content)
            
            # Extraer metadatos de herramientas
            metadata = {}
            tools_used = []
            
            for msg in final_state["messages"]:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_name = tc.get('name') if isinstance(tc, dict) else tc.name
                        tools_used.append(tool_name)
            
            if tools_used:
                metadata["tools_used"] = list(set(tools_used))
            
            print(f"   ✅ Respuesta generada")
            print(f"   📊 Herramientas: {metadata.get('tools_used', 'Ninguna')}")
            
            return WorkflowResult(
                content=content,
                workflow_type="agentic",
                metadata=metadata
            )
        
        except Exception as e:
            print(f"   ❌ Error en workflow agéntico: {e}")
            import traceback
            traceback.print_exc()
            return WorkflowResult(
                content=f"❌ Error: {str(e)}",
                workflow_type="agentic",
                metadata={"error": str(e)}
            )