"""
Workflows V2 (CONSOLIDADO + AUTONOMOUS OPTIMIZATION) - FIXED
Incluye:
1. WorkflowResult, FastPathWorkflow, AgenticWorkflow (Base)
2. SequentialWorkflow, ConversationWorkflow (V2)
3. AutonomousOptimizationWorkflow (NUEVO - FASE 2)

🔧 FIX: Añadido /invoke a todas las rutas de LangServe
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

# =======================================================
# 1. CLASES BASE
# =======================================================

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


class SequentialWorkflow:
    """Workflow SEQUENTIAL - Flujos multi-paso predefinidos."""
    
    def __init__(self, langserve_url: str, api_key: str, agent_app):
        self.langserve_url = langserve_url
        self.api_key = api_key
        self.agent_app = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """Ejecuta el flujo secuencial."""
        print(f"\n🔗 SEQUENTIAL WORKFLOW")
        print(f"   Query: '{query}'")
        
        agentic = AgenticWorkflow(self.agent_app)
        result = agentic.execute(query, thread_id)
        result.workflow_type = "sequential"
        
        return result


class ConversationWorkflow:
    """Workflow CONVERSACIONAL - Preguntas de seguimiento."""
    
    def __init__(self, agent_app):
        self.agent = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """Ejecuta pregunta de seguimiento."""
        print(f"\n💬 CONVERSATION WORKFLOW")
        print(f"   Query: '{query}'")
        print(f"   🧠 Usando memoria conversacional...")
        
        agentic = AgenticWorkflow(self.agent)
        result = agentic.execute(query, thread_id)
        result.workflow_type = "conversation"
        
        return result


# =======================================================
# 2. 🆕 AUTONOMOUS OPTIMIZATION WORKFLOW (FASE 2)
# =======================================================

class AutonomousOptimizationWorkflow:
    """
    🎯 WORKFLOW AUTÓNOMO DE OPTIMIZACIÓN (FASE 2)
    
    Flujo: Plan → Decide → Execute → Report
    
    1. Plan: Obtiene recomendaciones (GetCampaignRecommendations)
    2. Decide: Evalúa si ejecutar basado en:
       - Puntuación de oportunidad (opportunity_score >= threshold)
       - Prioridad (high/medium)
       - Modo autónomo (require_approval=False)
    3. Execute: Ejecuta acciones (UpdateAdsetBudget) si cumple criterios
    4. Report: Genera reporte de acciones tomadas
    """
    
    def __init__(
        self,
        langserve_url: str,
        api_key: str,
        agent_app,
        auto_execute_threshold: int = 3,
        require_approval: bool = False
    ):
        """
        Args:
            langserve_url: URL del servidor de herramientas
            api_key: API Key para autenticación
            agent_app: Instancia del agente LangGraph
            auto_execute_threshold: Puntos mínimos para ejecución automática (default: 3)
            require_approval: Si True, solo simula (default: False = modo autónomo)
        """
        self.langserve_url = langserve_url
        self.api_key = api_key
        self.agent_app = agent_app
        self.auto_execute_threshold = auto_execute_threshold
        self.require_approval = require_approval
        
        print(f"🤖 AutonomousOptimizationWorkflow inicializado:")
        print(f"   Umbral de ejecución: {auto_execute_threshold} puntos")
        print(f"   Modo: {'SIMULACIÓN' if require_approval else 'AUTÓNOMO'}")
    
    def execute(self, query: str, thread_id: str, campaign_id: Optional[str] = None) -> WorkflowResult:
        """
        Ejecuta el flujo autónomo de optimización.
        
        Args:
            query: Query del usuario (ej. "optimiza automáticamente mis campañas")
            thread_id: ID del thread para contexto
            campaign_id: ID de campaña específica o None para todas
            
        Returns:
            WorkflowResult con el reporte de acciones
        """
        print("\n" + "="*70)
        print("🎯 AUTONOMOUS OPTIMIZATION WORKFLOW")
        print("="*70)
        print(f"Query: '{query}'")
        print(f"Thread ID: {thread_id}")
        print(f"Campaign ID: {campaign_id or 'TODAS'}")
        print("="*70)
        
        try:
            # PASO 1: PLAN - Obtener recomendaciones
            print("\n📋 PASO 1: PLAN - Obteniendo recomendaciones...")
            recommendations = self._get_recommendations(campaign_id)
            
            if "error" in recommendations:
                return WorkflowResult(
                    content=f"❌ Error obteniendo recomendaciones: {recommendations['error']}",
                    workflow_type="autonomous_optimization",
                    metadata={"error": recommendations['error']}
                )
            
            total_campaigns = recommendations.get('campaigns_with_opportunities', 0)
            total_score = recommendations.get('total_opportunity_score', 0)
            
            print(f"   ✅ {total_campaigns} campañas con oportunidades")
            print(f"   📊 Puntuación total: {total_score}")
            
            if total_campaigns == 0:
                return WorkflowResult(
                    content="✅ No se encontraron oportunidades de optimización. Tus campañas están bien configuradas.",
                    workflow_type="autonomous_optimization",
                    metadata={"campaigns_analyzed": recommendations.get('total_campaigns_analyzed', 0)}
                )
            
            # PASO 2: DECIDE - Evaluar acciones a tomar
            print("\n🤔 PASO 2: DECIDE - Evaluando acciones...")
            actions_to_execute = self._decide_actions(recommendations)
            
            print(f"   📝 {len(actions_to_execute)} acciones identificadas")
            
            if not actions_to_execute:
                return self._generate_report(recommendations, [], "no_actions")
            
            # PASO 3: EXECUTE - Ejecutar acciones (si aplica)
            print("\n⚡ PASO 3: EXECUTE - Ejecutando acciones...")
            executed_actions = []
            
            for action in actions_to_execute:
                if self._should_execute(action):
                    result = self._execute_action(action)
                    executed_actions.append(result)
                else:
                    executed_actions.append({
                        **action,
                        "executed": False,
                        "reason": "Requiere aprobación manual o bajo umbral"
                    })
            
            # PASO 4: REPORT - Generar reporte
            print("\n📊 PASO 4: REPORT - Generando reporte...")
            return self._generate_report(recommendations, executed_actions, "completed")
        
        except Exception as e:
            print(f"\n❌ ERROR en workflow autónomo: {e}")
            import traceback
            traceback.print_exc()
            
            return WorkflowResult(
                content=f"❌ Error en optimización autónoma: {str(e)}",
                workflow_type="autonomous_optimization",
                metadata={"error": str(e)}
            )
    
    def _get_recommendations(self, campaign_id: Optional[str]) -> Dict[str, Any]:
        """
        ✅ FIX: Añadido /invoke
        Llama a GetCampaignRecommendations.
        """
        url = f"{self.langserve_url}/getcampaignrecommendations/invoke"
        headers = {"X-Tool-Api-Key": self.api_key, "Content-Type": "application/json"}
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"input": {"campana_id": campaign_id}},
                timeout=30
            )
            response.raise_for_status()
            
            output = response.json().get('output', {})
            datos_json = output.get('datos_json', '{}')
            
            return json.loads(datos_json)
        
        except Exception as e:
            return {"error": str(e)}
    
    def _decide_actions(self, recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evalúa recomendaciones y decide qué acciones ejecutar.
        
        Criterios:
        - Solo considera campañas con opportunity_score >= threshold
        - Prioriza recomendaciones de tipo "advantage_plus_audience" y "low_budget"
        """
        actions = []
        
        for campaign in recommendations.get('recommendations_by_campaign', []):
            campaign_id = campaign['campaign_id']
            campaign_name = campaign['campaign_name']
            opportunity_score = campaign['opportunity_score']
            
            # Filtrar por umbral
            if opportunity_score < self.auto_execute_threshold:
                print(f"   ⏭️  Skipping {campaign_name}: score {opportunity_score} < {self.auto_execute_threshold}")
                continue
            
            for rec in campaign['recommendations']:
                rec_type = rec['type']
                priority = rec['priority']
                
                # Solo actuar sobre tipos específicos
                if rec_type == "low_budget" and priority in ["high", "medium"]:
                    # Extraer adset name para buscar ID
                    adset_name = rec.get('adset', '')
                    
                    actions.append({
                        "type": "update_budget",
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "adset_name": adset_name,
                        "current_budget": rec.get('current_budget_eur', 5.0),
                        "recommended_budget": 15.0,  # Recomendación estándar
                        "reason": rec['title'],
                        "priority": priority,
                        "points": rec['points']
                    })
                
                elif rec_type == "advantage_plus_audience" and priority == "high":
                    # Esta acción requeriría una herramienta EnableAdvantageplus (pendiente ROL 2)
                    actions.append({
                        "type": "enable_advantage_plus",
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "adset_name": rec.get('adset', ''),
                        "reason": rec['title'],
                        "priority": priority,
                        "points": rec['points'],
                        "note": "⚠️ Herramienta EnableAdvantageplus pendiente (ROL 2)"
                    })
        
        return actions
    
    def _should_execute(self, action: Dict[str, Any]) -> bool:
        """Determina si una acción debe ejecutarse."""
        # Si require_approval está activo, nunca ejecutar automáticamente
        if self.require_approval:
            return False
        
        # Solo ejecutar acciones de tipo update_budget (las demás no están implementadas)
        if action['type'] != 'update_budget':
            return False
        
        # Verificar que tenga datos suficientes
        if not action.get('adset_name'):
            return False
        
        return True
    
    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una acción específica."""
        action_type = action['type']
        
        if action_type == "update_budget":
            return self._execute_budget_update(action)
        else:
            return {
                **action,
                "executed": False,
                "result": "Tipo de acción no soportado"
            }
    
    def _execute_budget_update(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        ✅ FIX: Añadido /invoke
        Ejecuta actualización de presupuesto vía UpdateAdsetBudget.
        """
        # Primero necesitamos obtener el adset_id desde el nombre
        # Esto requiere llamar a GetCampaignDetails
        
        try:
            # 1. Obtener detalles de la campaña para encontrar el adset_id
            details = self._get_campaign_details(action['campaign_id'])
            
            if "error" in details:
                return {
                    **action,
                    "executed": False,
                    "result": f"Error obteniendo detalles: {details['error']}"
                }
            
            # 2. Buscar el adset por nombre
            adset_id = None
            for adset in details.get('adsets', []):
                if action['adset_name'] in adset.get('adset_name', ''):
                    adset_id = adset['adset_id']
                    break
            
            if not adset_id:
                return {
                    **action,
                    "executed": False,
                    "result": f"No se encontró adset '{action['adset_name']}'"
                }
            
            # 3. Ejecutar UpdateAdsetBudget
            url = f"{self.langserve_url}/updateadsetbudget/invoke"
            headers = {"X-Tool-Api-Key": self.api_key, "Content-Type": "application/json"}
            
            response = requests.post(
                url,
                headers=headers,
                json={
                    "input": {
                        "adset_id": adset_id,
                        "new_daily_budget_eur": action['recommended_budget'],
                        "reason": f"Optimización autónoma: {action['reason']}"
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            
            output = response.json().get('output', {})
            
            return {
                **action,
                "executed": True,
                "adset_id": adset_id,
                "result": output.get('message', 'Actualizado'),
                "success": output.get('success', False)
            }
        
        except Exception as e:
            return {
                **action,
                "executed": False,
                "result": f"Error: {str(e)}"
            }
    
    def _get_campaign_details(self, campaign_id: str) -> Dict[str, Any]:
        """
        ✅ FIX: Añadido /invoke
        Obtiene detalles de una campaña.
        """
        url = f"{self.langserve_url}/getcampaigndetails/invoke"
        headers = {"X-Tool-Api-Key": self.api_key, "Content-Type": "application/json"}
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"input": {"campana_id": campaign_id, "include_adsets": True}},
                timeout=30
            )
            response.raise_for_status()
            
            output = response.json().get('output', {})
            datos_json = output.get('datos_json', '{}')
            
            return json.loads(datos_json)
        
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_report(
        self,
        recommendations: Dict[str, Any],
        executed_actions: List[Dict[str, Any]],
        status: str
    ) -> WorkflowResult:
        """Genera reporte final del workflow."""
        
        # Construir reporte
        report_parts = ["# 🎯 REPORTE DE OPTIMIZACIÓN AUTÓNOMA\n"]
        
        # Resumen ejecutivo
        total_campaigns = recommendations.get('campaigns_with_opportunities', 0)
        total_score = recommendations.get('total_opportunity_score', 0)
        
        report_parts.append(f"## 📊 Resumen Ejecutivo")
        report_parts.append(f"- **Campañas analizadas**: {recommendations.get('total_campaigns_analyzed', 0)}")
        report_parts.append(f"- **Campañas con oportunidades**: {total_campaigns}")
        report_parts.append(f"- **Puntuación total**: {total_score} puntos")
        report_parts.append(f"- **Acciones ejecutadas**: {len([a for a in executed_actions if a.get('executed')])}/{len(executed_actions)}\n")
        
        # Acciones ejecutadas
        if executed_actions:
            report_parts.append("## ⚡ Acciones Ejecutadas")
            
            for action in executed_actions:
                emoji = "✅" if action.get('executed') else "⏭️"
                action_type = action['type'].replace('_', ' ').title()
                
                report_parts.append(f"\n### {emoji} {action_type}")
                report_parts.append(f"- **Campaña**: {action['campaign_name']}")
                report_parts.append(f"- **Adset**: {action.get('adset_name', 'N/A')}")
                
                if action['type'] == 'update_budget':
                    report_parts.append(f"- **Presupuesto anterior**: {action.get('current_budget', 'N/A')}€")
                    report_parts.append(f"- **Presupuesto nuevo**: {action.get('recommended_budget', 'N/A')}€")
                
                report_parts.append(f"- **Razón**: {action['reason']}")
                report_parts.append(f"- **Estado**: {action.get('result', 'Pendiente')}")
        else:
            report_parts.append("\n## ℹ️ No se ejecutaron acciones")
            report_parts.append("- No se encontraron oportunidades que cumplan el umbral de ejecución")
            report_parts.append(f"- Umbral actual: {self.auto_execute_threshold} puntos")
        
        # Recomendaciones restantes
        report_parts.append("\n## 💡 Recomendaciones Adicionales")
        
        for campaign in recommendations.get('recommendations_by_campaign', [])[:3]:
            report_parts.append(f"\n**{campaign['campaign_name']}** ({campaign['opportunity_score']} puntos)")
            
            for rec in campaign['recommendations'][:2]:
                report_parts.append(f"- {rec['title']} (Prioridad: {rec['priority']})")
        
        # Footer
        report_parts.append(f"\n---")
        report_parts.append(f"*Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        report_parts.append(f"*Modo: {'SIMULACIÓN' if self.require_approval else 'AUTÓNOMO'}*")
        
        content = "\n".join(report_parts)
        
        metadata = {
            "total_campaigns": recommendations.get('total_campaigns_analyzed', 0),
            "campaigns_with_opportunities": total_campaigns,
            "total_opportunity_score": total_score,
            "actions_executed": len([a for a in executed_actions if a.get('executed')]),
            "actions_total": len(executed_actions),
            "status": status
        }
        
        return WorkflowResult(
            content=content,
            workflow_type="autonomous_optimization",
            metadata=metadata
        )


# =======================================================
# EXPORTACIÓN
# =======================================================

__all__ = [
    'WorkflowResult',
    'FastPathWorkflow',
    'AgenticWorkflow',
    'SequentialWorkflow',
    'ConversationWorkflow',
    'AutonomousOptimizationWorkflow',  # 🆕 FASE 2
]