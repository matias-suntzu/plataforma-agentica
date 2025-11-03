"""
Workflows - Día 1
Implementa Fast Path (Simple) y Agentic Workflow (Complejo)
"""

import os
import json
import requests
from typing import Dict, Any
from datetime import datetime


class WorkflowResult:
    """Resultado estandarizado de cualquier workflow."""
    
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
    """
    Workflow SIMPLE - Respuesta directa sin agente.
    Maneja consultas de estado y listados básicos.
    """
    
    def __init__(self, langserve_url: str, api_key: str):
        self.langserve_url = langserve_url
        self.api_key = api_key
    
    def execute(self, query: str) -> WorkflowResult:
        """
        Ejecuta el Fast Path para consultas simples.
        
        Args:
            query: La consulta del usuario
            
        Returns:
            WorkflowResult con la respuesta formateada
        """
        print(f"\n⚡ FAST PATH WORKFLOW")
        print(f"   Query: '{query}'")
        
        # Detectar tipo de consulta simple
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["listar", "lista", "todas las campañas", "campañas activas", "cuántas campañas"]):
            return self._listar_campanas()
        
        # Si no coincide con ningún patrón conocido, retornar mensaje genérico
        return WorkflowResult(
            content="⚠️ Consulta no reconocida en Fast Path. Redirigiendo a workflow complejo...",
            workflow_type="fast_path",
            metadata={"error": "unrecognized_pattern"}
        )
    
    def _listar_campanas(self) -> WorkflowResult:
        """Llama a la herramienta de listar campañas directamente."""
        
        try:
            url = f"{self.langserve_url}/listarcampanas/invoke"
            headers = {
                "Content-Type": "application/json",
                "X-Tool-Api-Key": self.api_key
            }
            payload = {
                "input": {
                    "placeholder": "obtener_campanas"
                }
            }
            
            print(f"   📡 Llamando a: {url}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                campanas_json = result.get('output', {}).get('campanas_json', '{}')
                campanas_data = json.loads(campanas_json)
                
                # Formatear respuesta
                if isinstance(campanas_data, list):
                    formatted = self._format_campanas(campanas_data)
                    
                    return WorkflowResult(
                        content=formatted,
                        workflow_type="fast_path",
                        metadata={
                            "total_campanas": len(campanas_data),
                            "tool_used": "ListarCampanasInput"
                        }
                    )
                else:
                    error_msg = campanas_data.get('error', 'Error desconocido')
                    return WorkflowResult(
                        content=f"❌ Error: {error_msg}",
                        workflow_type="fast_path",
                        metadata={"error": error_msg}
                    )
            
            else:
                error_detail = response.json().get('detail', 'Sin detalle')
                return WorkflowResult(
                    content=f"❌ Error del servidor: {error_detail}",
                    workflow_type="fast_path",
                    metadata={"http_status": response.status_code}
                )
        
        except requests.exceptions.RequestException as e:
            return WorkflowResult(
                content=f"❌ Error de conexión: {str(e)}",
                workflow_type="fast_path",
                metadata={"error": str(e)}
            )
        
        except Exception as e:
            return WorkflowResult(
                content=f"❌ Error inesperado: {str(e)}",
                workflow_type="fast_path",
                metadata={"error": str(e)}
            )
    
    def _format_campanas(self, campanas: list) -> str:
        """Formatea la lista de campañas en texto legible."""
        
        if not campanas:
            return "📭 No se encontraron campañas activas."
        
        output = f"📊 **Campañas de Meta Ads** ({len(campanas)} encontradas)\n\n"
        
        for i, camp in enumerate(campanas, 1):
            nombre = camp.get('name', 'Sin nombre')
            campaign_id = camp.get('id', 'N/A')
            status = camp.get('status', 'UNKNOWN')
            
            # Emoji según estado
            status_emoji = {
                'ACTIVE': '✅',
                'PAUSED': '⏸️',
                'ARCHIVED': '📦',
            }.get(status, '❓')
            
            output += f"{i}. {status_emoji} **{nombre}**\n"
            output += f"   ID: `{campaign_id}`\n"
            output += f"   Estado: {status}\n\n"
        
        return output


class AgenticWorkflow:
    """
    Workflow COMPLEJO - Usa el agente con herramientas.
    Maneja análisis, comparaciones, reportes, etc.
    """
    
    def __init__(self, agent_app):
        """
        Args:
            agent_app: La instancia compilada de tu agente actual (LangGraph app)
        """
        self.agent = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """
        Ejecuta el workflow agéntico completo.
        
        Args:
            query: La consulta del usuario
            thread_id: ID del thread para memoria persistente
            
        Returns:
            WorkflowResult con la respuesta del agente
        """
        print(f"\n🤖 AGENTIC WORKFLOW")
        print(f"   Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        
        try:
            from langchain_core.messages import HumanMessage
            
            # Configuración para memoria persistente
            config = {
                "configurable": {"thread_id": thread_id}
            }
            
            # Input del agente
            input_state = {
                "messages": [HumanMessage(content=query)]
            }
            
            # Ejecutar el agente
            print("   ⏳ Ejecutando agente...")
            result = self.agent.invoke(input_state, config=config)
            
            # Extraer el último mensaje del agente
            messages = result.get("messages", [])
            
            if not messages:
                return WorkflowResult(
                    content="❌ El agente no generó respuesta.",
                    workflow_type="agentic",
                    metadata={"error": "no_response"}
                )
            
            last_message = messages[-1]
            
            # Extraer contenido
            if hasattr(last_message, 'content'):
                content = last_message.content
            else:
                content = str(last_message)
            
            # Metadata del agente
            metadata = {
                "total_messages": len(messages),
                "thread_id": thread_id
            }
            
            # Detectar si se usaron herramientas
            tools_used = []
            for msg in messages:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_name = tc.get('name') if isinstance(tc, dict) else tc.name
                        tools_used.append(tool_name)
            
            if tools_used:
                metadata["tools_used"] = list(set(tools_used))
            
            print(f"   ✅ Respuesta generada")
            print(f"   📊 Herramientas usadas: {tools_used if tools_used else 'Ninguna'}")
            
            return WorkflowResult(
                content=content,
                workflow_type="agentic",
                metadata=metadata
            )
        
        except Exception as e:
            print(f"   ❌ Error en workflow agéntico: {e}")
            
            return WorkflowResult(
                content=f"❌ Error en el agente: {str(e)}",
                workflow_type="agentic",
                metadata={"error": str(e)}
            )


# Tests de validación
if __name__ == "__main__":
    print("🧪 Testing Workflows...")
    print("=" * 60)
    
    # Test Fast Path
    print("\n1️⃣ Testing Fast Path Workflow")
    fast_path = FastPathWorkflow(
        langserve_url=os.getenv("TOOL_SERVER_BASE_URL", "http://localhost:8000"),
        api_key=os.getenv("TOOL_API_KEY", "53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG")
    )
    
    result = fast_path.execute("lista todas las campañas")
    print(f"\n📄 Resultado:\n{result.content}")
    print(f"📊 Metadata: {result.metadata}")
    
    print("\n" + "="*60)
    print("✅ Tests completados")