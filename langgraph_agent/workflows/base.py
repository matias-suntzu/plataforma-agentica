"""
Workflows UNIFICADOS - Sin llamadas HTTP

✅ FastPathWorkflow: Llama funciones locales directamente
✅ AgenticWorkflow: Usa agent_app directamente
✅ SequentialWorkflow: Usa agent_app directamente
"""

import json
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Imports existentes
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig


# ========== WORKFLOW RESULT ==========

class WorkflowResult(BaseModel):
    """Resultado de un workflow"""
    content: str
    workflow_type: str
    metadata: Dict[str, Any] = {}


# ========== FASTPATH WORKFLOW ==========

class FastPathWorkflow:
    """
    Workflow optimizado para queries simples (sin agente).
    Llama funciones locales directamente (sin HTTP).
    """
    
    def __init__(self):
        print("⚡ FastPath iniciado (modo local, sin HTTP)")
    
    def execute(self, query: str) -> WorkflowResult:
        """Ejecuta query simple con herramientas locales"""
        query_lower = query.lower()
        
        # Caso 1: Listar campañas
        if any(kw in query_lower for kw in ["lista", "listar", "todas las campañas", "mis campañas"]):
            return self._listar_campanas()
        
        # Caso 2: Buscar campaña por nombre
        elif "busca" in query_lower or "id de" in query_lower:
            return self._buscar_campana(query)
        
        # Caso 3: Métricas globales
        elif any(kw in query_lower for kw in ["métricas", "rendimiento global", "todas las métricas"]):
            return self._metricas_globales()
        
        # Caso 4: No reconocido
        else:
            return WorkflowResult(
                content="⚠️ Query no reconocida para FastPath. Usar workflow agéntico.",
                workflow_type="simple",
                metadata={"fallback": True}
            )
    
    def _listar_campanas(self) -> WorkflowResult:
        """Lista campañas usando función local"""
        try:
            # Importar aquí para evitar imports circulares
            from ..tools.config.config_tools import listar_campanas_func, ListarCampanasInput
            
            result = listar_campanas_func(ListarCampanasInput())
            
            campanas = json.loads(result.campanas_json)
            
            if "error" in campanas:
                return WorkflowResult(
                    content=f"❌ Error: {campanas['error']}",
                    workflow_type="simple",
                    metadata={"error": campanas['error']}
                )
            
            # Formatear respuesta
            response = "📋 **Campañas activas:**\n\n"
            for camp in campanas:
                response += f"- **{camp['nombre']}** (ID: `{camp['id']}`) - {camp.get('estado', 'N/A')}\n"
            
            return WorkflowResult(
                content=response,
                workflow_type="simple",
                metadata={"campaigns_count": len(campanas)}
            )
        
        except Exception as e:
            return WorkflowResult(
                content=f"❌ Error: {str(e)}",
                workflow_type="simple",
                metadata={"error": str(e)}
            )
    
    def _buscar_campana(self, query: str) -> WorkflowResult:
        """Busca campaña por nombre"""
        try:
            from ..tools.config.config_tools import (
                buscar_campana_por_nombre_func,
                BuscarCampanaPorNombreInput
            )
            
            # Extraer nombre de la query
            nombre = self._extract_campaign_name(query)
            
            if not nombre:
                return WorkflowResult(
                    content="⚠️ No se pudo extraer nombre de campaña",
                    workflow_type="simple"
                )
            
            result = buscar_campana_por_nombre_func(
                BuscarCampanaPorNombreInput(nombre_campana=nombre)
            )
            
            if result.id_campana == "None":
                return WorkflowResult(
                    content=f"❌ No se encontró campaña: '{nombre}'",
                    workflow_type="simple"
                )
            
            return WorkflowResult(
                content=f"✅ Campaña encontrada:\n\n**{result.nombre_encontrado}**\nID: `{result.id_campana}`",
                workflow_type="simple",
                metadata={
                    "campaign_id": result.id_campana,
                    "campaign_name": result.nombre_encontrado
                }
            )
        
        except Exception as e:
            return WorkflowResult(
                content=f"❌ Error: {str(e)}",
                workflow_type="simple",
                metadata={"error": str(e)}
            )
    
    def _metricas_globales(self) -> WorkflowResult:
        """Obtiene métricas de todas las campañas"""
        try:
            from ..tools.performance.performance_tools import (
                obtener_metricas_globales_func,
                ObtenerMetricasGlobalesInput
            )
            
            result = obtener_metricas_globales_func(
                ObtenerMetricasGlobalesInput(date_preset="last_7d")
            )
            
            metrics = json.loads(result.datos_json)
            
            if "error" in metrics:
                return WorkflowResult(
                    content=f"❌ Error: {metrics['error']}",
                    workflow_type="simple",
                    metadata={"error": metrics['error']}
                )
            
            # Formatear respuesta
            response = f"""📊 **Métricas Globales (Últimos 7 días)**

💰 **Gasto Total:** {metrics.get('metricas_globales', {}).get('gasto_total_eur', 0):.2f}€
👆 **Clicks:** {metrics.get('metricas_globales', {}).get('clicks_total', 0):,}
👁️ **Impresiones:** {metrics.get('metricas_globales', {}).get('impresiones_total', 0):,}
🎯 **Conversiones:** {metrics.get('metricas_globales', {}).get('conversiones_total', 0)}

📈 **Promedios:**
- CPC: {metrics.get('metricas_globales', {}).get('cpc_promedio', 0):.2f}€
- CPA: {metrics.get('metricas_globales', {}).get('cpa_promedio', 0):.2f}€
- CTR: {metrics.get('metricas_globales', {}).get('ctr_promedio', 0):.2f}%

📋 **Campañas analizadas:** {metrics.get('campanas_analizadas', 0)}
"""
            
            return WorkflowResult(
                content=response,
                workflow_type="simple",
                metadata=metrics
            )
        
        except Exception as e:
            return WorkflowResult(
                content=f"❌ Error: {str(e)}",
                workflow_type="simple",
                metadata={"error": str(e)}
            )
    
    def _extract_campaign_name(self, query: str) -> Optional[str]:
        """Extrae nombre de campaña de la query"""
        # Patrones comunes
        patterns = [
            "busca ",
            "buscar ",
            "id de ",
            "campaña ",
            "campaña de ",
        ]
        
        query_lower = query.lower()
        
        for pattern in patterns:
            if pattern in query_lower:
                idx = query_lower.index(pattern)
                nombre = query[idx + len(pattern):].strip()
                return nombre.replace('"', '').replace("'", '')
        
        return None


# ========== AGENTIC WORKFLOW ==========

class AgenticWorkflow:
    """
    Workflow agéntico con LangGraph.
    Usa agent_app directamente.
    """
    
    def __init__(self, agent_app):
        self.agent_app = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """Ejecuta query con agente completo"""
        try:
            config = RunnableConfig(configurable={"thread_id": thread_id})
            input_message = HumanMessage(content=query)
            
            result = self.agent_app.invoke(
                {"messages": [input_message]},
                config=config
            )
            
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
            return WorkflowResult(
                content=f"❌ Error en agente: {str(e)}",
                workflow_type="agentic",
                metadata={"error": str(e)}
            )


# ========== SEQUENTIAL WORKFLOW ==========

class SequentialWorkflow:
    """
    Workflow secuencial (multi-paso).
    """
    
    def __init__(self, agent_app):
        self.agent_app = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """
        Ejecuta workflow multi-paso.
        Si necesita herramientas, el agente las llamará directamente.
        """
        return self._execute_with_agent(query, thread_id)
    
    def _execute_with_agent(self, query: str, thread_id: str) -> WorkflowResult:
        """Delega al agente (ya tiene acceso a herramientas)"""
        try:
            config = RunnableConfig(configurable={"thread_id": thread_id})
            input_message = HumanMessage(content=query)
            
            result = self.agent_app.invoke(
                {"messages": [input_message]},
                config=config
            )
            
            final_message = result["messages"][-1]
            content = final_message.content if isinstance(final_message.content, str) else str(final_message.content)
            
            return WorkflowResult(
                content=content,
                workflow_type="sequential",
                metadata={"thread_id": thread_id}
            )
        
        except Exception as e:
            return WorkflowResult(
                content=f"❌ Error: {str(e)}",
                workflow_type="sequential",
                metadata={"error": str(e)}
            )


# ========== CONVERSATION WORKFLOW ==========

class ConversationWorkflow:
    """Workflow conversacional"""
    
    def __init__(self, agent_app):
        self.agent_app = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """Igual que AgenticWorkflow"""
        agentic = AgenticWorkflow(self.agent_app)
        return agentic.execute(query, thread_id)