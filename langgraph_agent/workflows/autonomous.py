"""
Autonomous Optimization Workflow - VERSIÓN UNIFICADA (sin HTTP)
"""
from .base import WorkflowResult
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

# ✅ Importar herramientas LOCALES
from ..tools.recommendations import (
    get_campaign_recommendations_func,
    get_campaign_details_func
)
from ..tools.actions import update_adset_budget_func
from ..models.schemas import (
    GetCampaignRecommendationsInput,
    GetCampaignDetailsInput,
    UpdateAdsetBudgetInput
)


class AutonomousOptimizationWorkflow:
    """
    🎯 WORKFLOW AUTÓNOMO DE OPTIMIZACIÓN (FASE 2) - UNIFICADO
    
    Flujo: Plan → Decide → Execute → Report
    """
    
    def __init__(
        self,
        agent_app,
        auto_execute_threshold: int = 3,
        require_approval: bool = False
    ):
        """
        ✅ CAMBIO: Ya NO recibe langserve_url ni api_key
        
        Args:
            agent_app: Instancia del agente LangGraph
            auto_execute_threshold: Puntos mínimos para ejecución automática (default: 3)
            require_approval: Si True, solo simula (default: False = modo autónomo)
        """
        self.agent_app = agent_app
        self.auto_execute_threshold = auto_execute_threshold
        self.require_approval = require_approval
        
        print(f"🤖 AutonomousOptimizationWorkflow inicializado:")
        print(f"   Umbral de ejecución: {auto_execute_threshold} puntos")
        print(f"   Modo: {'SIMULACIÓN' if require_approval else 'AUTÓNOMO'}")
    
    def execute(self, query: str, thread_id: str, campaign_id: Optional[str] = None) -> WorkflowResult:
        """
        Ejecuta el flujo autónomo de optimización.
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
        ✅ Llama a GetCampaignRecommendations LOCAL (sin HTTP).
        """
        try:
            input_data = GetCampaignRecommendationsInput(campana_id=campaign_id)
            result = get_campaign_recommendations_func(input_data)
            
            # El resultado viene en result.datos_json
            return json.loads(result.datos_json)
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"error": str(e)}
    
    def _decide_actions(self, recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evalúa recomendaciones y decide qué acciones ejecutar.
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
                    adset_name = rec.get('adset', '')
                    
                    actions.append({
                        "type": "update_budget",
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "adset_name": adset_name,
                        "current_budget": rec.get('current_budget_eur', 5.0),
                        "recommended_budget": 15.0,
                        "reason": rec['title'],
                        "priority": priority,
                        "points": rec['points']
                    })
                
                elif rec_type == "advantage_plus_audience" and priority == "high":
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
        if self.require_approval:
            return False
        
        if action['type'] != 'update_budget':
            return False
        
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
        ✅ Ejecuta actualización de presupuesto LOCAL (sin HTTP).
        """
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
            
            # 3. Ejecutar UpdateAdsetBudget LOCAL
            input_data = UpdateAdsetBudgetInput(
                adset_id=adset_id,
                new_daily_budget_eur=action['recommended_budget'],
                reason=f"Optimización autónoma: {action['reason']}"
            )
            
            result = update_adset_budget_func(input_data)
            
            return {
                **action,
                "executed": True,
                "adset_id": adset_id,
                "result": result.message,
                "success": result.success
            }
        
        except Exception as e:
            return {
                **action,
                "executed": False,
                "result": f"Error: {str(e)}"
            }
    
    def _get_campaign_details(self, campaign_id: str) -> Dict[str, Any]:
        """
        ✅ Obtiene detalles de una campaña LOCAL (sin HTTP).
        """
        try:
            input_data = GetCampaignDetailsInput(
                campana_id=campaign_id,
                include_adsets=True
            )
            result = get_campaign_details_func(input_data)
            
            return json.loads(result.datos_json)
        
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_report(
        self,
        recommendations: Dict[str, Any],
        executed_actions: List[Dict[str, Any]],
        status: str
    ) -> WorkflowResult:
        """Genera reporte final del workflow."""
        
        report_parts = ["# 🎯 REPORTE DE OPTIMIZACIÓN AUTÓNOMA\n"]
        
        total_campaigns = recommendations.get('campaigns_with_opportunities', 0)
        total_score = recommendations.get('total_opportunity_score', 0)
        
        report_parts.append(f"## 📊 Resumen Ejecutivo")
        report_parts.append(f"- **Campañas analizadas**: {recommendations.get('total_campaigns_analyzed', 0)}")
        report_parts.append(f"- **Campañas con oportunidades**: {total_campaigns}")
        report_parts.append(f"- **Puntuación total**: {total_score} puntos")
        report_parts.append(f"- **Acciones ejecutadas**: {len([a for a in executed_actions if a.get('executed')])}/{len(executed_actions)}\n")
        
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
        
        report_parts.append("\n## 💡 Recomendaciones Adicionales")
        
        for campaign in recommendations.get('recommendations_by_campaign', [])[:3]:
            report_parts.append(f"\n**{campaign['campaign_name']}** ({campaign['opportunity_score']} puntos)")
            
            for rec in campaign['recommendations'][:2]:
                report_parts.append(f"- {rec['title']} (Prioridad: {rec['priority']})")
        
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