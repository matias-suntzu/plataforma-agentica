"""
Orchestrator V3 (CONSOLIDADO + COMPARACIÓN DE PERÍODOS)
"""

import os
import uuid
import json
import time
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Importar mensajes de LangChain
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage  # ← AÑADE ESTO


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
from ..safety.guardrails import GuardrailsManager, ValidationResult
from ..safety.anomaly_detector import AnomalyDetector, AnomalySeverity
from ..memory.caching import CacheManager, QueryCache, ToolCache

load_dotenv()

# =======================================================
# ORCHESTRATORV3 (CONSOLIDADO + FASE 2)
# =======================================================

class OrchestratorV3:
    """
    Orchestrator V3 consolidado con:
    - Routing inteligente (V2)
    - Workflows complejos (V2)
    - Seguridad (Guardrails, Rate Limiting)
    - Optimización (Caching)
    - Detección de anomalías
    - 🆕 Comparación de períodos (FASE 2)
    - 🆕 Optimización autónoma (FASE 2)
    """
    
    def __init__(
        self,
        enable_logging: bool = True,
        enable_guardrails: bool = True,
        enable_caching: bool = True,
        enable_anomaly_detection: bool = True
    ):
        print("🚀 Inicializando Orchestrator V3 (FASE 2)...")
        
        # Configuración base
        langserve_url = os.getenv("TOOL_SERVER_BASE_URL", "http://localhost:8000")
        api_key = os.getenv("TOOL_API_KEY", "53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG")
        
        self.langserve_url = langserve_url
        self.api_key = api_key
        self.enable_logging = enable_logging
        self.log_file = "orchestrator_v3_metrics.jsonl"
        
        # Router V2
        self.router = QueryRouterV3(log_to_file=enable_logging)
        
        # Workflows base
        self.fast_path = FastPathWorkflow(langserve_url, api_key)
        self.sequential = SequentialWorkflow(langserve_url, api_key, agent_app)
        self.agentic = AgenticWorkflow(agent_app)
        self.conversation = ConversationWorkflow(agent_app)
        
        # 🆕 FASE 2: Autonomous Optimization Workflow
        self.autonomous_workflow = AutonomousOptimizationWorkflow(
            langserve_url=langserve_url,
            api_key=api_key,
            agent_app=agent_app,
            auto_execute_threshold=3,  # Ejecutar si opportunity_score >= 3
            require_approval=False     # Modo autónomo (True = solo simulación)
        )
        
        # Métricas
        self.metrics = {
            "simple": {"count": 0, "total_time": 0},
            "sequential": {"count": 0, "total_time": 0},
            "agentic": {"count": 0, "total_time": 0},
            "conversation": {"count": 0, "total_time": 0},
            "blocked": {"count": 0, "total_time": 0},
            "cached": {"count": 0, "total_time": 0},
            "autonomous_optimization": {"count": 0, "total_time": 0},  # 🆕
            "period_comparison": {"count": 0, "total_time": 0}  # 🆕
        }
        
        # Sistemas de robustez
        self.enable_guardrails = enable_guardrails
        if self.enable_guardrails:
            self.guardrails = GuardrailsManager()
        
        self.enable_caching = enable_caching
        if self.enable_caching:
            self.cache_manager = CacheManager(cache_dir="cache", default_ttl=1800)
            self.query_cache = QueryCache(self.cache_manager, ttl=1800)
            self.tool_cache = ToolCache(self.cache_manager, ttl=3600)
        
        self.enable_anomaly_detection = enable_anomaly_detection
        if self.enable_anomaly_detection:
            self.anomaly_detector = AnomalyDetector(
                cpa_threshold=50.0,
                ctr_min_threshold=0.5,
                spend_threshold=1000.0
            )

        print("✅ Orchestrator V3 listo (FASE 2)")
        print("   🎯 Nuevas capacidades:")
        print("      - Comparación de períodos")
        print("      - Optimización autónoma")
        print()

    # =======================================================
    # 🆕 TAREA 3.2: COMPARACIÓN DE PERÍODOS
    # =======================================================
    
    def _detect_comparison_query(self, query: str) -> Optional[Dict[str, str]]:
        """
        Detecta si una query es de comparación de períodos.
        
        Returns:
            Dict con period1 y period2 si es comparación, None si no lo es
        """
        query_lower = query.lower()
        
        # Patrones de comparación
        comparison_patterns = [
            (r'compar.*semana.*anterior', {'period1': 'last_7d', 'period2': '7_days_prior'}),
            (r'compar.*esta.*semana.*pasada', {'period1': 'last_7d', 'period2': '7_days_prior'}),
            (r'compar.*mes.*anterior', {'period1': 'last_30d', 'period2': '30_days_prior'}),
            (r'compar.*este.*mes.*pasado', {'period1': 'last_30d', 'period2': '30_days_prior'}),
            (r'vs.*semana.*pasada', {'period1': 'last_7d', 'period2': '7_days_prior'}),
            (r'vs.*mes.*pasado', {'period1': 'last_30d', 'period2': '30_days_prior'}),
            (r'compar.*con la anterior', {'period1': 'last_7d', 'period2': '7_days_prior'}),
        ]
        
        for pattern, periods in comparison_patterns:
            if re.search(pattern, query_lower):
                return periods
        
        return None
    
    def compare_periods(
        self,
        period1: str,
        period2: str,
        thread_id: str
    ) -> WorkflowResult:
        """
        🆕 TAREA 3.2: Compara métricas entre dos períodos.
        
        Flujo:
        1. Obtener métricas del período 1 (GetAllCampaignsMetrics)
        2. Obtener métricas del período 2 (GetAllCampaignsMetrics)
        3. Calcular deltas (%, absolutos)
        4. Pasar al LLM para análisis y recomendaciones
        
        Args:
            period1: Período reciente (ej. 'last_7d')
            period2: Período anterior (ej. '7_days_prior')
            thread_id: ID del thread
            
        Returns:
            WorkflowResult con el análisis comparativo
        """
        print("\n" + "="*70)
        print("📊 COMPARACIÓN DE PERÍODOS")
        print("="*70)
        print(f"Período 1 (reciente): {period1}")
        print(f"Período 2 (anterior): {period2}")
        print("="*70)
        
        try:
            # PASO 1: Obtener métricas del período 1
            print("\n📈 Obteniendo métricas del período reciente...")
            metrics1 = self._get_period_metrics(period1)
            
            if "error" in metrics1:
                return WorkflowResult(
                    content=f"❌ Error obteniendo métricas del período 1: {metrics1['error']}",
                    workflow_type="period_comparison",
                    metadata={"error": metrics1['error']}
                )
            
            # PASO 2: Obtener métricas del período 2
            print("📉 Obteniendo métricas del período anterior...")
            metrics2 = self._get_period_metrics(period2)
            
            if "error" in metrics2:
                return WorkflowResult(
                    content=f"❌ Error obteniendo métricas del período 2: {metrics2['error']}",
                    workflow_type="period_comparison",
                    metadata={"error": metrics2['error']}
                )
            
            # PASO 3: Calcular deltas
            print("🧮 Calculando diferencias...")
            comparison = self._calculate_deltas(metrics1, metrics2)
            
            # PASO 4: Análisis con LLM
            print("🤖 Generando análisis con LLM...")
            analysis = self._analyze_comparison_with_llm(comparison, thread_id)
            
            return WorkflowResult(
                content=analysis,
                workflow_type="period_comparison",
                metadata={
                    "period1": period1,
                    "period2": period2,
                    "comparison_data": comparison
                }
            )
        
        except Exception as e:
            print(f"\n❌ ERROR en comparación: {e}")
            import traceback
            traceback.print_exc()
            
            return WorkflowResult(
                content=f"❌ Error en comparación de períodos: {str(e)}",
                workflow_type="period_comparison",
                metadata={"error": str(e)}
            )
    
    def _get_period_metrics(self, period: str) -> Dict[str, Any]:
        """Obtiene métricas de un período específico."""
        import requests
        
        # Manejar períodos especiales como '7_days_prior'
        if '_prior' in period:
            # Calcular fechas custom
            days_ago = int(period.split('_')[0])
            end_date = datetime.now() - timedelta(days=days_ago)
            start_date = end_date - timedelta(days=days_ago)
            
            date_start = start_date.strftime('%Y-%m-%d')
            date_end = end_date.strftime('%Y-%m-%d')
            
            payload = {
                "input": {
                    "date_start": date_start,
                    "date_end": date_end,
                    "metrics": ["spend", "clicks", "impressions", "conversions"]
                }
            }
        else:
            payload = {
                "input": {
                    "date_preset": period,
                    "metrics": ["spend", "clicks", "impressions", "conversions"]
                }
            }
        
        url = f"{self.langserve_url}/getallcampaignsmetrics/invoke"
        headers = {"X-Tool-Api-Key": self.api_key, "Content-Type": "application/json"}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            output = response.json().get('output', {})
            datos_json = output.get('datos_json', '{}')
            
            return json.loads(datos_json)
        
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_deltas(self, metrics1: Dict, metrics2: Dict) -> Dict[str, Any]:
        """Calcula diferencias entre dos períodos."""
        
        # Extraer totales
        spend1 = metrics1.get('total_spend', 0)
        spend2 = metrics2.get('total_spend', 0)
        
        clicks1 = metrics1.get('total_clicks', 0)
        clicks2 = metrics2.get('total_clicks', 0)
        
        impressions1 = metrics1.get('total_impressions', 0)
        impressions2 = metrics2.get('total_impressions', 0)
        
        conversions1 = metrics1.get('total_conversions', 0)
        conversions2 = metrics2.get('total_conversions', 0)
        
        cpa1 = metrics1.get('avg_cpa', 0)
        cpa2 = metrics2.get('avg_cpa', 0)
        
        ctr1 = metrics1.get('avg_ctr', 0)
        ctr2 = metrics2.get('avg_ctr', 0)
        
        # Calcular cambios porcentuales
        def calc_change(current, previous):
            if previous == 0:
                return 0
            return round(((current - previous) / previous) * 100, 2)
        
        comparison = {
            "period1": {
                "spend": round(spend1, 2),
                "clicks": clicks1,
                "impressions": impressions1,
                "conversions": conversions1,
                "avg_cpa": round(cpa1, 2),
                "avg_ctr": round(ctr1, 2)
            },
            "period2": {
                "spend": round(spend2, 2),
                "clicks": clicks2,
                "impressions": impressions2,
                "conversions": conversions2,
                "avg_cpa": round(cpa2, 2),
                "avg_ctr": round(ctr2, 2)
            },
            "deltas": {
                "spend_change_pct": calc_change(spend1, spend2),
                "spend_change_abs": round(spend1 - spend2, 2),
                "clicks_change_pct": calc_change(clicks1, clicks2),
                "clicks_change_abs": clicks1 - clicks2,
                "impressions_change_pct": calc_change(impressions1, impressions2),
                "impressions_change_abs": impressions1 - impressions2,
                "conversions_change_pct": calc_change(conversions1, conversions2),
                "conversions_change_abs": conversions1 - conversions2,
                "cpa_change_pct": calc_change(cpa1, cpa2),
                "cpa_change_abs": round(cpa1 - cpa2, 2),
                "ctr_change_pct": calc_change(ctr1, ctr2),
                "ctr_change_abs": round(ctr1 - ctr2, 2)
            }
        }
        
        return comparison
    
    def _analyze_comparison_with_llm(self, comparison: Dict, thread_id: str) -> str:
        """Analiza la comparación con el LLM."""
        from langchain_core.messages import HumanMessage
        from langchain_core.runnables import RunnableConfig
        
        # Crear prompt para el LLM
        prompt = f"""Analiza esta comparación de períodos de Meta Ads y proporciona insights accionables.

## DATOS DE COMPARACIÓN

### Período Reciente:
- Gasto: {comparison['period1']['spend']}€
- Clicks: {comparison['period1']['clicks']}
- Impresiones: {comparison['period1']['impressions']}
- Conversiones: {comparison['period1']['conversions']}
- CPA promedio: {comparison['period1']['avg_cpa']}€
- CTR promedio: {comparison['period1']['avg_ctr']}%

### Período Anterior:
- Gasto: {comparison['period2']['spend']}€
- Clicks: {comparison['period2']['clicks']}
- Impresiones: {comparison['period2']['impressions']}
- Conversiones: {comparison['period2']['conversions']}
- CPA promedio: {comparison['period2']['avg_cpa']}€
- CTR promedio: {comparison['period2']['avg_ctr']}%

### CAMBIOS (% y absolutos):
- Gasto: {comparison['deltas']['spend_change_pct']:+.1f}% ({comparison['deltas']['spend_change_abs']:+.2f}€)
- Clicks: {comparison['deltas']['clicks_change_pct']:+.1f}% ({comparison['deltas']['clicks_change_abs']:+d})
- Impresiones: {comparison['deltas']['impressions_change_pct']:+.1f}% ({comparison['deltas']['impressions_change_abs']:+d})
- Conversiones: {comparison['deltas']['conversions_change_pct']:+.1f}% ({comparison['deltas']['conversions_change_abs']:+d})
- CPA: {comparison['deltas']['cpa_change_pct']:+.1f}% ({comparison['deltas']['cpa_change_abs']:+.2f}€)
- CTR: {comparison['deltas']['ctr_change_pct']:+.1f}% ({comparison['deltas']['ctr_change_abs']:+.2f}%)

## INSTRUCCIONES:
1. Identifica las métricas que mejoraron (usa ✅) y las que empeoraron (usa ⚠️)
2. Explica las causas probables de los cambios significativos (>20%)
3. Proporciona 3 recomendaciones accionables específicas
4. Formato: Markdown con emojis para facilitar lectura

Responde de forma concisa y accionable."""

        try:
            config = RunnableConfig(configurable={"thread_id": thread_id})
            input_message = HumanMessage(content=prompt)
            
            result = agent_app.invoke({"messages": [input_message]}, config=config)
            final_message = result["messages"][-1]
            
            if isinstance(final_message.content, str):
                return final_message.content
            elif isinstance(final_message.content, list):
                return "\n".join([str(item) for item in final_message.content])
            else:
                return str(final_message.content)
        
        except Exception as e:
            # Fallback: generar reporte básico sin LLM
            return self._generate_basic_comparison_report(comparison)
    
    def _generate_basic_comparison_report(self, comparison: Dict) -> str:
        """Genera reporte básico si el LLM falla."""
        report = ["# 📊 COMPARACIÓN DE PERÍODOS\n"]
        
        deltas = comparison['deltas']
        
        # Análisis de gasto
        if deltas['spend_change_pct'] > 0:
            report.append(f"⚠️ **Gasto aumentó** {deltas['spend_change_pct']:+.1f}% ({deltas['spend_change_abs']:+.2f}€)")
        else:
            report.append(f"✅ **Gasto disminuyó** {deltas['spend_change_pct']:+.1f}% ({deltas['spend_change_abs']:+.2f}€)")
        
        # Análisis de conversiones
        if deltas['conversions_change_pct'] > 0:
            report.append(f"✅ **Conversiones aumentaron** {deltas['conversions_change_pct']:+.1f}% ({deltas['conversions_change_abs']:+d})")
        else:
            report.append(f"⚠️ **Conversiones disminuyeron** {deltas['conversions_change_pct']:+.1f}% ({deltas['conversions_change_abs']:+d})")
        
        # Análisis de CPA
        if deltas['cpa_change_pct'] < 0:
            report.append(f"✅ **CPA mejoró** {deltas['cpa_change_pct']:+.1f}% ({deltas['cpa_change_abs']:+.2f}€)")
        else:
            report.append(f"⚠️ **CPA empeoró** {deltas['cpa_change_pct']:+.1f}% ({deltas['cpa_change_abs']:+.2f}€)")
        
        return "\n".join(report)

    # =======================================================
    # CORE WORKFLOW EXECUTION
    # =======================================================
    
    def _execute_core_workflow(
        self,
        query: str,
        thread_id: str,
        force_workflow: Optional[str],
    ) -> WorkflowResult:
        """Ejecuta la lógica central de routing y workflow."""
        
        # 🆕 PASO 0: Detectar comparación de períodos ANTES del router
        comparison_params = self._detect_comparison_query(query)
        if comparison_params:
            print("🔍 Query de comparación detectada")
            return self.compare_periods(
                period1=comparison_params['period1'],
                period2=comparison_params['period2'],
                thread_id=thread_id
            )
        
        # 🆕 PASO 0b: Detectar optimización autónoma
        autonomous_keywords = ["optimiza automáticamente", "mejora automática", "optimización autónoma"]
        if any(kw in query.lower() for kw in autonomous_keywords):
            print("🔍 Query de optimización autónoma detectada")
            return self.autonomous_workflow.execute(query, thread_id)
        
        # PASO 1: Clasificar la consulta (routing normal)
        if force_workflow:
            category = force_workflow
            route_result = None
        else:
            route_result = self.router.classify(query)
            category = route_result.category
        
        # PASO 2: Ejecutar el workflow correspondiente
        if category == "simple":
            result = self.fast_path.execute(query)
        elif category == "sequential":
            result = self.sequential.execute(query, thread_id)
        elif category == "agentic":
            result = self.agentic.execute(query, thread_id)
        elif category == "conversation":
            result = self.conversation.execute(query, thread_id)

        elif category == "PERIOD_COMPARISON":
            print("🔍 Router clasificó como PERIOD_COMPARISON. Ejecutando comparación...")
            # Re-ejecutar la detección para obtener los parámetros del período
            comparison_params = self._detect_comparison_query(query)

            if comparison_params:
                result = self.compare_periods(
                    period1=comparison_params['period1'],
                    period2=comparison_params['period2'],
                    thread_id=thread_id
                )
            else:
                # Fallback si el Router clasifica bien, pero no se extraen los períodos (poco probable)
                result = WorkflowResult(
                    content="❌ El Router clasificó como comparación, pero no se pudieron detectar los períodos.",
                    workflow_type="error",
                    metadata={"error": "comparison_params_not_found"}
                )

        else:
            result = WorkflowResult(
                content=f"❌ Categoría desconocida: {category}",
                workflow_type="error",
                metadata={"error": "unknown_category"}
            )
        
        # Agregar metadatos del router
        if route_result:
            result.metadata["router_confidence"] = route_result.confidence
            result.metadata["router_category"] = route_result.category
        
        return result
    
    def process_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        user_id: str = "default",
        force_workflow: Optional[str] = None,
        skip_cache: bool = False
    ) -> WorkflowResult:
        """
        Procesa una consulta con todos los sistemas de seguridad (V3 + FASE 2).
        """
        start_time = datetime.now()
        
        if not thread_id:
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*70)
        print(f"🔥 NUEVA CONSULTA (V3 FASE 2)")
        print(f"   Query: '{query}' | User: {user_id} | Thread: {thread_id}")
        print("="*70)
        
        try:
            # PASO 1: GUARDRAILS DE ENTRADA
            if self.enable_guardrails:
                validation = self.guardrails.validate_input(query, user_id)
                
                if not validation.is_valid:
                    self.metrics["blocked"]["count"] += 1
                    return WorkflowResult(
                        content=f"❌ Consulta bloqueada: {validation.reason}",
                        workflow_type="blocked",
                        metadata={"blocked_by": "input_guardrails", "reason": validation.reason}
                    )
            
            # PASO 2: VERIFICAR CACHÉ
            if self.enable_caching and not skip_cache:
                cached_response = self.query_cache.get_cached_response(query)
                
                if cached_response:
                    self.metrics["cached"]["count"] += 1
                    return WorkflowResult(
                        content=cached_response,
                        workflow_type="cached",
                        metadata={"cache_hit": True}
                    )
            
            # PASO 3: EJECUTAR CORE WORKFLOW
            result = self._execute_core_workflow(query, thread_id, force_workflow)
            
            # PASO 3b: Actualizar métricas
            end_time_core = datetime.now()
            elapsed_time_core = (end_time_core - start_time).total_seconds()
            
            if result.workflow_type in self.metrics:
                self.metrics[result.workflow_type]["count"] += 1
                self.metrics[result.workflow_type]["total_time"] += elapsed_time_core
            
            # PASO 4: GUARDRAILS DE SALIDA
            if self.enable_guardrails:
                output_validation = self.guardrails.validate_output(result.content)
                
                if not output_validation.is_valid:
                    self.metrics["blocked"]["count"] += 1
                    return WorkflowResult(
                        content="❌ Respuesta bloqueada por seguridad.",
                        workflow_type="blocked",
                        metadata={"blocked_by": "output_guardrails"}
                    )
            
            # PASO 5: DETECCIÓN DE ANOMALÍAS
            if self.enable_anomaly_detection and result.workflow_type in ["agentic", "sequential"]:
                self._check_for_anomalies(result)
            
            # PASO 6: CACHEAR RESPUESTA
            if self.enable_caching and result.workflow_type not in ["error", "blocked", "conversation"]:
                self.query_cache.cache_response(query, result.content)
            
            # PASO 7: Logging
            elapsed_time_total = (datetime.now() - start_time).total_seconds()
            self._log_query(query, result.workflow_type, result, elapsed_time_total, user_id)
            
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

    # =======================================================
    # MÉTRICAS Y UTILIDADES
    # =======================================================
    
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
        print("📊 MÉTRICAS DEL ORCHESTRATOR V3 (FASE 2)")
        print("="*70)
        
        total_queries = sum(m["total_queries"] for m in metrics.values())
        
        print(f"\n📈 Total de consultas procesadas: {total_queries}")
        print()
        
        emoji_map = {
            "simple": "⚡",
            "sequential": "🔗",
            "agentic": "🤖",
            "conversation": "💬",
            "blocked": "🚫",
            "cached": "💾",
            "autonomous_optimization": "🎯",
            "period_comparison": "📊"
        }
        
        for category, data in metrics.items():
            if data["total_queries"] > 0:
                emoji = emoji_map.get(category, "❓")
                
                print(f"{emoji} {category.upper()}:")
                print(f"   Consultas: {data['total_queries']}")
                print(f"   Tiempo promedio: {data['avg_time']:.2f}s")
                print(f"   Tiempo total: {data['total_time']:.2f}s")
                print()
        
        print("="*70)
    
    def _log_query(self, query: str, category: str, result: WorkflowResult, elapsed_time: float, user_id: str):
        """Guarda métricas en archivo JSONL."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "user_id": user_id,
            "category": category,
            "workflow_type": result.workflow_type,
            "elapsed_time": elapsed_time,
            "router_confidence": result.metadata.get("router_confidence"),
            "metadata": result.metadata
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ Error al guardar log: {e}")
    
    def _check_for_anomalies(self, result: WorkflowResult) -> list:
        """Lógica de detección de anomalías (placeholder)."""
        return []
    
    def shutdown(self):
        """Limpieza al cerrar el orchestrator."""
        print("\n🛑 Cerrando Orchestrator V3...")
        
        if self.enable_caching:
            self.cache_manager.save_to_disk()
        
        if self.enable_guardrails:
            self.guardrails.save_violations_log()
        
        if self.enable_anomaly_detection:
            self.anomaly_detector.save_to_file()
        
        self.print_metrics()
        print("✅ Orchestrator V3 cerrado correctamente")
    
    def chat(self, thread_id: Optional[str] = None):
        """Modo interactivo de chat."""
        if not thread_id:
            thread_id = f"interactive_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*70)
        print("💬 MODO CHAT INTERACTIVO V3 (FASE 2)")
        print("="*70)
        print(f"Thread ID: {thread_id}")
        print("\nComandos especiales:")
        print("  - 'salir' / 'exit' / 'quit': Terminar sesión")
        print("  - 'nuevo': Iniciar nueva conversación")
        print("  - 'metrics': Ver estadísticas")
        print("\nEjemplos de queries:")
        print("  - 'compara esta semana con la anterior'")
        print("  - 'optimiza automáticamente mis campañas'")
        print("  - 'dame el TOP 3 de Baqueira'")
        print("="*70 + "\n")
        
        while True:
            try:
                user_input = input("👤 Tú: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['salir', 'exit', 'quit']:
                    self.print_metrics()
                    print("\n👋 ¡Hasta luego!")
                    break
                
                if user_input.lower() == 'nuevo':
                    thread_id = f"interactive_{uuid.uuid4().hex[:8]}"
                    print(f"\n🔄 Nueva conversación iniciada (Thread: {thread_id})\n")
                    continue
                
                if user_input.lower() == 'metrics':
                    self.print_metrics()
                    continue
                
                # Procesar la consulta
                result = self.process_query(user_input, thread_id=thread_id)
                
                # Mostrar respuesta
                print(f"\n🤖 Agente ({result.workflow_type}):")
                print(result.content)
                print("\n" + "-"*70 + "\n")
            
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrupción detectada")
                self.print_metrics()
                break
            
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                import traceback
                traceback.print_exc()


# =======================================================
# SCRIPTS DE PRUEBA
# =======================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        print("\n🎯 DEMO ORCHESTRATOR V3 (FASE 2)\n")
        
        orch = OrchestratorV3()
        
        queries = [
            "lista todas las campañas",
            "compara esta semana con la anterior",
            "optimiza automáticamente mis campañas",
            "dame el TOP 3 de Baqueira",
        ]
        
        for query in queries:
            print(f"\n{'='*70}")
            print(f"QUERY: {query}")
            print('='*70)
            result = orch.process_query(query, user_id="demo_user")
            print(f"\n✅ Resultado ({result.workflow_type}):")
            print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
            print("-" * 70)
        
        orch.shutdown()
    
    elif len(sys.argv) > 1 and sys.argv[1] == "chat":
        orchestrator = OrchestratorV3()
        orchestrator.chat()
        
    else:
        print("\n📖 Uso de orchestrator_v3.py:")
        print("="*50)
        print("  python -m langgraph_agent.orchestrator_v3 demo  (Demo)")
        print("  python -m langgraph_agent.orchestrator_v3 chat  (Interactivo)")
        print("="*50)
