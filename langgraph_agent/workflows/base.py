"""
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

class FastPathWorkflow:
    """Workflow SIMPLE - Respuesta directa sin agente."""
    
    def __init__(self, langserve_url: str, api_key: str):
        self.langserve_url = langserve_url
        self.api_key = api_key
    
    def _call_tool_server(self, path: str, input_data: Dict[str, Any]) -> str:
        """
        ✅ FIX: Añadido /invoke al final de la ruta
        """
        # ✅ CORRECTO: Asegurar que path termine en /invoke
        if not path.endswith('/invoke'):
            path = f"{path}/invoke"
        
        url = f"{self.langserve_url}{path}"
        headers = {"X-Tool-Api-Key": self.api_key, "Content-Type": "application/json"}
        
        try:
            print(f"   ⚙️ Llamando a la herramienta Fast Path: {url}")
            response = requests.post(url, headers=headers, json={"input": input_data}, timeout=15)
            response.raise_for_status()
            
            tool_output = response.json().get("output", "Respuesta de herramienta no encontrada.")
            
            if isinstance(tool_output, dict):
                return json.dumps(tool_output, indent=2)
            return tool_output
            
        except requests.exceptions.HTTPError as e:
            return f"Error HTTP: {e.response.status_code}"
        except Exception as e:
            return f"Error en FastPath: {str(e)}"

    def execute(self, query: str) -> WorkflowResult:
        """Ejecuta el Fast Path."""
        print(f"\n⚡ FAST PATH WORKFLOW")
        print(f"   Query: '{query}'")

        # ✅ Path sin /invoke - se añade automáticamente en _call_tool_server
        tool_output = self._call_tool_server("/listarcampanas", {})
        
        content = (
            "🤖 Llamada directa a `listarcampanas`."
            f"\n\n**Resultado:**\n```json\n{tool_output[:2000]}...\n```"
        )
        
        return WorkflowResult(
            content=content,
            workflow_type="simple",
            metadata={"tool_used": "/listarcampanas"}
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
            # ✅ CORRECTO: Dejar que LangGraph maneje la serialización automáticamente
            config = {"configurable": {"thread_id": thread_id}}
            input_message = HumanMessage(content=query)
            
            # Invocar el agente SIN intentar serializar manualmente
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

