"""
Workflows UNIFICADOS - Sin llamadas HTTP

CAMBIOS:
1. FastPathWorkflow ya no recibe langserve_url ni api_key
2. Importa y llama funciones locales directamente
"""

import json
from typing import Dict, Any, Optional
from pydantic import BaseModel

# ✅ NUEVO: Importar herramientas locales
from ..tools import (
    listar_campanas_func,
    buscar_id_campana_func,
    get_all_campaigns_metrics_func
)

# ✅ NUEVO: Importar schemas
from ..models.schemas import (
    ListarCampanasInput,
    BuscarIdCampanaInput,
    GetAllCampaignsMetricsInput
)

# Imports existentes
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig


class WorkflowResult(BaseModel):
    """Resultado de un workflow"""
    content: str
    workflow_type: str
    metadata: Dict[str, Any] = {}


# =======================================================
# ✅ FASTPATHWORKFLOW MODIFICADO
# =======================================================

class FastPathWorkflow:
    """
    Workflow optimizado para queries simples (sin agente).
    
    ✅ CAMBIO: Ya no usa HTTP, llama funciones locales
    """
    
    def __init__(self):
        """
        ✅ CAMBIO: Ya no recibe langserve_url ni api_key
        """
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
    
    # ✅ MÉTODOS MODIFICADOS (llamadas locales)
    
    def _listar_campanas(self) -> WorkflowResult:
        """Lista campañas usando función local"""
        try:
            # ✅ LLAMADA LOCAL (antes era HTTP)
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
                response += f"- **{camp['name']}** (ID: `{camp['id']}`) - {camp.get('status', 'N/A')}\n"
            
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
            # Extraer nombre de la query
            nombre = self._extract_campaign_name(query)
            
            if not nombre:
                return WorkflowResult(
                    content="⚠️ No se pudo extraer nombre de campaña",
                    workflow_type="simple"
                )
            
            # ✅ LLAMADA LOCAL
            result = buscar_id_campana_func(
                BuscarIdCampanaInput(nombre_campana=nombre)
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
            # ✅ LLAMADA LOCAL
            result = get_all_campaigns_metrics_func(
                GetAllCampaignsMetricsInput(date_preset="last_7d")
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

💰 **Gasto Total:** {metrics.get('total_spend', 0):.2f}€
👆 **Clicks:** {metrics.get('total_clicks', 0):,}
👁️ **Impresiones:** {metrics.get('total_impressions', 0):,}
🎯 **Conversiones:** {metrics.get('total_conversions', 0)}

📈 **Promedios:**
- CPC: {metrics.get('avg_cpc', 0):.2f}€
- CPA: {metrics.get('avg_cpa', 0):.2f}€
- CTR: {metrics.get('avg_ctr', 0):.2f}%

📋 **Campañas analizadas:** {metrics.get('campaigns_analyzed', 0)}
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


# =======================================================
# OTROS WORKFLOWS (AgenticWorkflow, SequentialWorkflow)
# =======================================================

class AgenticWorkflow:
    """
    Workflow agéntico con LangGraph.
    ✅ Ya no necesita modificaciones (usa agent_app directamente)
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


class SequentialWorkflow:
    """
    Workflow secuencial (multi-paso).
    ✅ CAMBIO: Ya no recibe langserve_url
    """
    
    def __init__(self, agent_app):
        self.agent_app = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """
        Ejecuta workflow multi-paso.
        Si necesita herramientas, el agente las llamará directamente.
        """
        # Similar a AgenticWorkflow pero con pasos intermedios
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


class ConversationWorkflow:
    """Workflow conversacional (sin cambios)"""
    
    def __init__(self, agent_app):
        self.agent_app = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        # Igual que AgenticWorkflow
        pass