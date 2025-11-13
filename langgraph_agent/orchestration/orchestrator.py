"""
Orchestrator V3 (CONSOLIDADO + COMPARACIÓN DE PERÍODOS) - VERSIÓN UNIFICADA
"""

import os
import uuid
import json
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Importar Router V3 y Workflows
from .router import QueryRouterV3
from ..workflows.base import (
    FastPathWorkflow,
    AgenticWorkflow,
    WorkflowResult
)
from ..workflows.sequential import SequentialWorkflow
from ..workflows.conversation import ConversationWorkflow
from ..workflows.autonomous import AutonomousOptimizationWorkflow

# Importar el agente compilado
from ..core.agent import app as agent_app

# Importar sistemas del Día 3
from ..safety.guardrails import GuardrailsManager
from ..safety.anomaly_detector import AnomalyDetector
from ..memory.caching import CacheManager, QueryCache, ToolCache

# ✅ Importar herramientas locales
from ..tools.metrics import get_all_campaigns_metrics_func
from ..models.schemas import GetAllCampaignsMetricsInput

load_dotenv()


class OrchestratorV3:
    """
    Orchestrator V3 UNIFICADO - Sin dependencia de Tool Server externo
    """
    
    def __init__(
        self,
        enable_logging: bool = True,
        enable_guardrails: bool = True,
        enable_caching: bool = True,
        enable_anomaly_detection: bool = True
    ):
        print("🚀 Inicializando Orchestrator V3 UNIFICADO...")
        
        self.enable_logging = enable_logging
        self.log_file = "orchestrator_v3_metrics.jsonl"
        
        # Router V3
        self.router = QueryRouterV3(log_to_file=enable_logging)
        
        # ✅ Workflows ya NO reciben langserve_url ni api_key
        self.fast_path = FastPathWorkflow()
        self.sequential = SequentialWorkflow(agent_app)
        self.agentic = AgenticWorkflow(agent_app)
        self.conversation = ConversationWorkflow(agent_app)
        
        # Autonomous workflow
        self.autonomous_workflow = AutonomousOptimizationWorkflow(
            agent_app=agent_app,
            auto_execute_threshold=3,
            require_approval=False
        )
        
        # Métricas
        self.metrics = {
            "simple": {"count": 0, "total_time": 0},
            "sequential": {"count": 0, "total_time": 0},
            "agentic": {"count": 0, "total_time": 0},
            "conversation": {"count": 0, "total_time": 0},
            "blocked": {"count": 0, "total_time": 0},
            "cached": {"count": 0, "total_time": 0},
            "autonomous_optimization": {"count": 0, "total_time": 0},
            "period_comparison": {"count": 0, "total_time": 0}
        }
        
        # Sistemas de robustez
        self.enable_guardrails = enable_guardrails
        if self.enable_guardrails:
            try:
                self.guardrails = GuardrailsManager()
            except Exception as e:
                print(f"⚠️ Guardrails no disponible: {e}")
                self.enable_guardrails = False
        
        self.enable_caching = enable_caching
        if self.enable_caching:
            try:
                self.cache_manager = CacheManager(cache_dir="cache", default_ttl=1800)
                self.query_cache = QueryCache(self.cache_manager, ttl=1800)
                self.tool_cache = ToolCache(self.cache_manager, ttl=3600)
            except Exception as e:
                print(f"⚠️ Caching no disponible: {e}")
                self.enable_caching = False
        
        self.enable_anomaly_detection = enable_anomaly_detection
        if self.enable_anomaly_detection:
            try:
                self.anomaly_detector = AnomalyDetector(
                    cpa_threshold=50.0,
                    ctr_min_threshold=0.5,
                    spend_threshold=1000.0
                )
            except Exception as e:
                print(f"⚠️ Anomaly detection no disponible: {e}")
                self.enable_anomaly_detection = False

        print("✅ Orchestrator V3 UNIFICADO listo")
        print()

    def _detect_comparison_query(self, query: str) -> Optional[Dict[str, str]]:
        """Detecta si una query es de comparación de períodos."""
        query_lower = query.lower()
        
        comparison_patterns = [
            (r'compar.*semana.*anterior', {'period1': 'last_7d', 'period2': '7_days_prior'}),
            (r'compar.*esta.*semana.*pasada', {'period1': 'last_7d', 'period2': '7_days_prior'}),
            (r'compar.*mes.*anterior', {'period1': 'last_30d', 'period2': '30_days_prior'}),
            (r'vs.*semana.*pasada', {'period1': 'last_7d', 'period2': '7_days_prior'}),
        ]
        
        for pattern, periods in comparison_patterns:
            if re.search(pattern, query_lower):
                return periods
        
        return None
    
    def _get_period_metrics(self, period: str) -> Dict[str, Any]:
        """Obtiene métricas de un período específico usando herramienta LOCAL."""
        
        try:
            # Manejar períodos especiales como '7_days_prior'
            if '_prior' in period:
                days_ago = int(period.split('_')[0])
                end_date = datetime.now() - timedelta(days=days_ago)
                start_date = end_date - timedelta(days=days_ago)
                
                date_start = start_date.strftime('%Y-%m-%d')
                date_end = end_date.strftime('%Y-%m-%d')
                
                input_data = GetAllCampaignsMetricsInput(
                    date_preset='last_7d',  # Requerido por el schema
                    # date_start=date_start,  # Si el schema lo soporta
                    # date_end=date_end,
                )
            else:
                input_data = GetAllCampaignsMetricsInput(
                    date_preset=period,
                )
            
            # ✅ Llamada LOCAL
            result = get_all_campaigns_metrics_func(input_data)
            return json.loads(result.datos_json)
        
        except Exception as e:
            print(f"❌ Error obteniendo métricas: {e}")
            return {"error": str(e)}
    
    def _execute_core_workflow(
        self,
        query: str,
        thread_id: str,
        force_workflow: Optional[str],
    ) -> WorkflowResult:
        """Ejecuta la lógica central de routing y workflow."""
        
        # Detectar comparación de períodos
        comparison_params = self._detect_comparison_query(query)
        if comparison_params:
            print("🔍 Query de comparación detectada")
            # TODO: Implementar compare_periods
            return WorkflowResult(
                content="Comparación de períodos detectada (pendiente implementación)",
                workflow_type="period_comparison",
                metadata=comparison_params
            )
        
        # Detectar optimización autónoma
        autonomous_keywords = ["optimiza automáticamente", "mejora automática", "optimización autónoma"]
        if any(kw in query.lower() for kw in autonomous_keywords):
            print("🔍 Query de optimización autónoma detectada")
            return self.autonomous_workflow.execute(query, thread_id)
        
        # Clasificar la consulta
        if force_workflow:
            category = force_workflow
        else:
            route_result = self.router.classify(query)
            category = route_result.category
        
        # Ejecutar el workflow correspondiente
        if category == "simple":
            result = self.fast_path.execute(query)
        elif category == "sequential":
            result = self.sequential.execute(query, thread_id)
        elif category == "agentic":
            result = self.agentic.execute(query, thread_id)
        elif category == "conversation":
            result = self.conversation.execute(query, thread_id)
        else:
            result = WorkflowResult(
                content=f"❌ Categoría desconocida: {category}",
                workflow_type="error",
                metadata={"error": "unknown_category"}
            )
        
        return result
    
    def process_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        user_id: str = "default",
        force_workflow: Optional[str] = None,
        skip_cache: bool = False
    ) -> WorkflowResult:
        """Procesa una consulta con todos los sistemas de seguridad."""
        
        start_time = datetime.now()
        
        if not thread_id:
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*70)
        print(f"🔥 NUEVA CONSULTA (V3 UNIFICADO)")
        print(f"   Query: '{query}' | User: {user_id} | Thread: {thread_id}")
        print("="*70)
        
        try:
            # Guardrails de entrada
            if self.enable_guardrails:
                validation = self.guardrails.validate_input(query, user_id)
                if not validation.is_valid:
                    self.metrics["blocked"]["count"] += 1
                    return WorkflowResult(
                        content=f"❌ Consulta bloqueada: {validation.reason}",
                        workflow_type="blocked",
                        metadata={"blocked_by": "input_guardrails"}
                    )
            
            # Verificar caché
            if self.enable_caching and not skip_cache:
                cached_response = self.query_cache.get_cached_response(query)
                if cached_response:
                    self.metrics["cached"]["count"] += 1
                    return WorkflowResult(
                        content=cached_response,
                        workflow_type="cached",
                        metadata={"cache_hit": True}
                    )
            
            # Ejecutar workflow
            result = self._execute_core_workflow(query, thread_id, force_workflow)
            
            # Actualizar métricas
            elapsed_time = (datetime.now() - start_time).total_seconds()
            if result.workflow_type in self.metrics:
                self.metrics[result.workflow_type]["count"] += 1
                self.metrics[result.workflow_type]["total_time"] += elapsed_time
            
            # Cachear respuesta
            if self.enable_caching and result.workflow_type not in ["error", "blocked", "conversation"]:
                self.query_cache.cache_response(query, result.content)
            
            return result
        
        except Exception as e:
            print(f"\n❌ ERROR EN ORCHESTRATOR: {e}")
            import traceback
            traceback.print_exc()
            return WorkflowResult(
                content=f"❌ Error inesperado: {str(e)}",
                workflow_type="error",
                metadata={"error": str(e)}
            )
    
    def get_metrics(self) -> dict:
        """Retorna métricas agregadas."""
        metrics_summary = {}
        
        for category, data in self.metrics.items():
            count = data["count"]
            total_time = data["total_time"]
            
            metrics_summary[category] = {
                "total_queries": count,
                "total_time": round(total_time, 2),
                "avg_time": round(total_time / count, 2) if count > 0 else 0
            }
        
        return metrics_summary
    
    def print_metrics(self):
        """Imprime métricas de rendimiento."""
        metrics = self.get_metrics()
        
        print("\n" + "="*70)
        print("📊 MÉTRICAS DEL ORCHESTRATOR V3")
        print("="*70)
        
        total_queries = sum(m["total_queries"] for m in metrics.values())
        print(f"\n📈 Total de consultas procesadas: {total_queries}\n")
        
        for category, data in metrics.items():
            if data["total_queries"] > 0:
                print(f"{category.upper()}:")
                print(f"   Consultas: {data['total_queries']}")
                print(f"   Tiempo promedio: {data['avg_time']:.2f}s")
                print()
        
        print("="*70)