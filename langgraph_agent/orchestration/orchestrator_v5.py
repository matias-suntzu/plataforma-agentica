"""
Orchestrator V5 - Multi-Agente con Recomendaciones
Agrega RecommendationAgent al sistema
"""

import uuid
from datetime import datetime
from typing import Optional
from langchain_core.messages import HumanMessage, BaseMessage
from typing import List

from .router_v4 import router_v4
from ..agents.coordinator_agent import coordinator
from ..agents.config_agent import config_agent
from ..agents.performance_agent import performance_agent
from ..agents.recommendation_agent import recommendation_agent  # ✨ NUEVO
from ..workflows.base import WorkflowResult, FastPathWorkflow


class OrchestratorV5:
    """
    Orchestrator con 4 agentes especializados:
    - ConfigAgent
    - PerformanceAgent
    - RecommendationAgent ✨
    - Multi-Agent (combinación)
    
    Flujo:
    1. Router V4 clasifica en: simple / agentic / multi_agent
    2. Si simple → FastPath (sin agente)
    3. Si agentic → Coordinator decide entre Config/Performance/Recommendation
    4. Si multi_agent → Ejecuta los agentes necesarios y combina respuestas
    """
    
    def __init__(self, enable_logging: bool = True):
        print("🚀 Inicializando Orchestrator V5 (con Recommendations)...")
        
        self.router = router_v4
        self.coordinator = coordinator
        self.config_agent = config_agent
        self.performance_agent = performance_agent
        self.recommendation_agent = recommendation_agent  # ✨
        self.fast_path = FastPathWorkflow()
        
        self.enable_logging = enable_logging
        
        # Métricas
        self.metrics = {
            "simple": {"count": 0, "total_time": 0},
            "agentic_config": {"count": 0, "total_time": 0},
            "agentic_performance": {"count": 0, "total_time": 0},
            "agentic_recommendation": {"count": 0, "total_time": 0},  # ✨
            "multi_agent": {"count": 0, "total_time": 0},
        }
        
        print("✅ Orchestrator V5 listo (4 agentes)")
        print()
    
    def process_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        force_workflow: Optional[str] = None,
        messages: Optional[List[BaseMessage]] = None
    ) -> WorkflowResult:
        """
        Procesa una consulta con arquitectura multi-agente (4 agentes).
        
        Args:
            query: Consulta del usuario
            thread_id: ID del thread para memoria (opcional)
            force_workflow: Forzar workflow específico (opcional)
            
        Returns:
            WorkflowResult con la respuesta
        """
        start_time = datetime.now()
        
        if not thread_id:
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*70)
        print(f"🔥 NUEVA CONSULTA (V5 - 4 Agentes)")
        print(f"   Query: '{query}' | Thread: {thread_id}")
        print("="*70)
        
        try:
            # PASO 1: Clasificar con Router V4
            if force_workflow:
                category = force_workflow
                print(f"   ⚙️ Forzando workflow: {category}")
            else:
                route_result = self.router.classify(query)
                category = route_result.category
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # PASO 2: Ejecutar según categoría
            if category == "simple":
                # FastPath sin agente
                result = self.fast_path.execute(query)
                workflow_type = "simple"
            
            elif category == "agentic":
                # Usar Coordinator para decidir agente
                coord_decision = self.coordinator.route(query)
                
                if coord_decision.agent == "config":
                    result = self._execute_single_agent(
                        self.config_agent, query, config, "agentic_config"
                    )
                    workflow_type = "agentic_config"
                
                elif coord_decision.agent == "performance":
                    result = self._execute_single_agent(
                        self.performance_agent, query, config, "agentic_performance"
                    )
                    workflow_type = "agentic_performance"
                
                elif coord_decision.agent == "recommendation":  # ✨ NUEVO
                    result = self._execute_single_agent(
                        self.recommendation_agent, query, config, "agentic_recommendation"
                    )
                    workflow_type = "agentic_recommendation"
                
                else:  # multi
                    result = self._execute_multi_agent(query, config)
                    workflow_type = "multi_agent"
            
            elif category == "multi_agent":
                # Ejecutar varios agentes directamente
                result = self._execute_multi_agent(query, config)
                workflow_type = "multi_agent"
            
            else:
                result = WorkflowResult(
                    content=f"❌ Categoría desconocida: {category}",
                    workflow_type="error",
                    metadata={"error": "unknown_category"}
                )
                workflow_type = "error"
            
            # Actualizar métricas
            elapsed_time = (datetime.now() - start_time).total_seconds()
            if workflow_type in self.metrics:
                self.metrics[workflow_type]["count"] += 1
                self.metrics[workflow_type]["total_time"] += elapsed_time
            
            print(f"\n✅ Respuesta generada en {elapsed_time:.2f}s")
            print(f"   Workflow: {workflow_type}")
            print("="*70)
            
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
    
    def _execute_single_agent(
        self, 
        agent, 
        query: str, 
        config: dict, 
        workflow_type: str
    ) -> WorkflowResult:
        """Ejecuta un solo agente"""
        agent_result = agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        final_message = agent_result["messages"][-1]
        content = final_message.content if isinstance(final_message.content, str) else str(final_message.content)
        
        return WorkflowResult(
            content=content,
            workflow_type=workflow_type,
            metadata={"agent": workflow_type.split("_")[1]}
        )
    
    def _execute_multi_agent(self, query: str, config: dict) -> WorkflowResult:
        """
        Ejecuta múltiples agentes y combina respuestas.
        
        Decide inteligentemente qué agentes usar:
        - Si menciona "recomendaciones" → Config + Recommendation
        - Si pide "análisis completo" → Config + Performance + Recommendation
        - Si ambiguo → Config + Performance
        """
        print("\n⚙️ MULTI-AGENT MODE: Analizando qué agentes usar...")
        
        query_lower = query.lower()
        
        # Detectar qué agentes necesitamos
        needs_config = True  # Casi siempre necesitamos config
        needs_performance = any(kw in query_lower for kw in [
            "gasto", "clicks", "conversiones", "rendimiento", "ctr", "cpm", "cpa"
        ])
        needs_recommendation = any(kw in query_lower for kw in [
            "recomienda", "optimiza", "mejora", "sugerencia", "debería", "completo", "análisis"
        ])
        
        # Si no detectamos nada específico, usar config + performance por defecto
        if not needs_performance and not needs_recommendation:
            needs_performance = True
        
        agents_used = []
        responses = {}
        
        # Ejecutar Config
        if needs_config:
            print("   📋 Llamando a ConfigAgent...")
            config_result = self.config_agent.invoke(
                {"messages": [HumanMessage(content=query)]},
                config=config
            )
            responses["config"] = config_result["messages"][-1].content
            agents_used.append("config")
        
        # Ejecutar Performance
        if needs_performance:
            print("   📈 Llamando a PerformanceAgent...")
            perf_result = self.performance_agent.invoke(
                {"messages": [HumanMessage(content=query)]},
                config=config
            )
            responses["performance"] = perf_result["messages"][-1].content
            agents_used.append("performance")
        
        # Ejecutar Recommendation ✨
        if needs_recommendation:
            print("   💡 Llamando a RecommendationAgent...")
            rec_result = self.recommendation_agent.invoke(
                {"messages": [HumanMessage(content=query)]},
                config=config
            )
            responses["recommendation"] = rec_result["messages"][-1].content
            agents_used.append("recommendation")
        
        # Combinar respuestas
        combined_content = self._combine_responses(responses, agents_used)
        
        return WorkflowResult(
            content=combined_content.strip(),
            workflow_type="multi_agent",
            metadata={"agents_used": agents_used}
        )
    
    def _combine_responses(self, responses: dict, agents_used: list) -> str:
        """Combina respuestas de múltiples agentes en formato bonito"""
        sections = []
        
        if "config" in responses:
            sections.append(f"""## 📋 Configuración Técnica
{responses["config"]}""")
        
        if "performance" in responses:
            sections.append(f"""## 📈 Rendimiento
{responses["performance"]}""")
        
        if "recommendation" in responses:
            sections.append(f"""## 💡 Recomendaciones
{responses["recommendation"]}""")
        
        header = f"# ⚙️ ANÁLISIS COMPLETO ({len(agents_used)} agentes)\n\n"
        
        return header + "\n\n---\n\n".join(sections)
    
    def get_metrics(self) -> dict:
        """Retorna métricas agregadas"""
        metrics_summary = {}
        
        for workflow_type, data in self.metrics.items():
            count = data["count"]
            total_time = data["total_time"]
            
            metrics_summary[workflow_type] = {
                "total_queries": count,
                "total_time": round(total_time, 2),
                "avg_time": round(total_time / count, 2) if count > 0 else 0
            }
        
        return metrics_summary
    
    def print_metrics(self):
        """Imprime métricas de rendimiento"""
        metrics = self.get_metrics()
        
        print("\n" + "="*70)
        print("📈 MÉTRICAS DEL ORCHESTRATOR V5")
        print("="*70)
        
        total_queries = sum(m["total_queries"] for m in metrics.values())
        print(f"\n📊 Total de consultas procesadas: {total_queries}\n")
        
        for workflow_type, data in metrics.items():
            if data["total_queries"] > 0:
                print(f"{workflow_type.upper()}:")
                print(f"   Consultas: {data['total_queries']}")
                print(f"   Tiempo promedio: {data['avg_time']:.2f}s")
                print()
        
        print("="*70)


# ========== EXPORTAR ==========

orchestrator_v5 = OrchestratorV5()


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing Orchestrator V5...\n")
    
    test_queries = [
        ("lista todas las campañas", "simple"),
        ("¿qué presupuesto tiene Baqueira?", "agentic_config"),
        ("gasto de Ibiza esta semana", "agentic_performance"),
        ("dame recomendaciones para mejorar el CPA de Baqueira", "agentic_recommendation"),  # ✨
        ("analiza la campaña de Costa Blanca con sugerencias", "multi_agent"),
    ]
    
    for query, expected_workflow in test_queries:
        print(f"\n{'='*70}")
        print(f"Testing: {query}")
        print('='*70)
        
        result = orchestrator_v5.process_query(query)
        
        print(f"\nWorkflow usado: {result.workflow_type}")
        print(f"Esperado: {expected_workflow}")
        
        if result.workflow_type == expected_workflow:
            print("✅ TEST PASADO")
        else:
            print("❌ TEST FALLIDO")
        
        print(f"\nRespuesta (primeros 200 chars):\n{result.content[:200]}...")
    
    # Mostrar métricas finales
    orchestrator_v5.print_metrics()