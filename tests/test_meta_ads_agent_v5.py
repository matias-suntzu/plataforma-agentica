"""
Suite Completa de Testing para Meta Ads Agent V5
=================================================

Valida:
- Router V4: Clasificación correcta (simple/agentic/multi_agent)
- Coordinator: Routing entre agentes (config/performance/recommendation)
- ConfigAgent: Herramientas de configuración
- PerformanceAgent: Herramientas de rendimiento + ANUNCIOS
- RecommendationAgent: Recomendaciones de optimización
- OrchestratorV5: Flujo completo end-to-end
- Casos edge: Continuaciones, contexto conversacional, "todas las campañas"

Ejecutar: python test_meta_ads_agent_v5.py
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Importar componentes del sistema
from langgraph_agent.orchestration.orchestrator_v5 import orchestrator_v5
from langgraph_agent.orchestration.router_v4 import router_v4
from langgraph_agent.agents.coordinator_agent import coordinator
from langgraph_agent.agents.config_agent import config_agent
from langgraph_agent.agents.performance_agent import performance_agent
from langgraph_agent.agents.recommendation_agent import recommendation_agent

from langchain_core.messages import HumanMessage, AIMessage


# ========== CONFIGURACIÓN ==========

@dataclass
class TestCase:
    """Caso de prueba con validación"""
    query: str
    expected_router: str = None  # Ahora es opcional
    expected_coordinator: str = None
    expected_agent: str = None
    description: str = ""
    context: List = None
    should_use_tool: str = None


# ========== TEST CASES ==========

# 🔥 CRÍTICO: Testing de Anuncios (Nueva Funcionalidad)
ANUNCIOS_TEST_CASES = [
    TestCase(
        query="¿Qué anuncio tiene el mejor CTR en Costa Blanca?",
        expected_router="agentic",
        expected_coordinator="performance",
        expected_agent="performance",
        should_use_tool="ObtenerAnunciosPorRendimientoInput",
        description="🔥 RANKING: Mejor anuncio por métrica específica"
    ),
    TestCase(
        query="¿Hay algún anuncio que ha empeorado y que explique el cambio en el CPA?",
        expected_router="agentic",
        expected_coordinator="performance",
        expected_agent="performance",
        should_use_tool="CompararAnunciosInput",
        description="🔥 COMPARACIÓN TEMPORAL: Identificar anuncios que empeoraron"
    ),
    TestCase(
        query="Dame todos los anuncios de Baqueira",
        expected_router="agentic",
        expected_coordinator="performance",
        expected_agent="performance",
        should_use_tool="ObtenerAnunciosPorRendimientoInput",
        description="🔥 LISTADO COMPLETO: Todos los anuncios (limite=100)"
    ),
    TestCase(
        query="¿Qué anuncio explica el aumento del CPA?",
        expected_router="agentic",
        expected_coordinator="performance",
        expected_agent="performance",
        should_use_tool="CompararAnunciosInput",
        description="🔥 ANÁLISIS: Anuncio que causa cambio en métrica"
    ),
    TestCase(
        query="TOP 3 anuncios con mejor CPA en Ibiza",
        expected_router="agentic",
        expected_coordinator="performance",
        expected_agent="performance",
        should_use_tool="ObtenerAnunciosPorRendimientoInput",
        description="🔥 TOP N: Ranking con métrica ordenar_por=cpa"
    ),
    TestCase(
        query="¿Cuál anuncio tiene peor rendimiento?",
        expected_router="agentic",
        expected_coordinator="performance",
        expected_agent="performance",
        should_use_tool="ObtenerAnunciosPorRendimientoInput",
        description="🔥 PEOR: Ordenamiento inverso"
    ),
]

# Router V4: Clasificación Simple/Agentic/Multi
ROUTER_TEST_CASES = [
    # SIMPLE (FastPath)
    TestCase(
        query="lista todas las campañas",
        expected_router="simple",
        description="Listado simple sin métricas"
    ),
    TestCase(
        query="¿cuántas campañas activas tengo?",
        expected_router="simple",
        description="Conteo simple"
    ),
    
    # AGENTIC (Config)
    TestCase(
        query="¿qué presupuesto tiene Baqueira?",
        expected_router="agentic",
        expected_coordinator="config",
        description="Configuración específica"
    ),
    TestCase(
        query="estrategia de puja de Ibiza",
        expected_router="agentic",
        expected_coordinator="config",
        description="Config técnica"
    ),
    
    # AGENTIC (Performance)
    TestCase(
        query="¿cuánto he gastado en Costa Blanca esta semana?",
        expected_router="agentic",
        expected_coordinator="performance",
        description="Métrica de rendimiento"
    ),
    TestCase(
        query="conversiones de Menorca últimos 7 días",
        expected_router="agentic",
        expected_coordinator="performance",
        description="Métrica específica"
    ),
    TestCase(
        query="compara esta semana con la anterior",
        expected_router="agentic",
        expected_coordinator="performance",
        description="Comparación de períodos"
    ),
    
    # AGENTIC (Recommendation)
    TestCase(
        query="dame recomendaciones para mejorar el CPA de Baqueira",
        expected_router="agentic",
        expected_coordinator="recommendation",
        description="Recomendación específica"
    ),
    TestCase(
        query="¿debería activar Advantage+ en Ibiza?",
        expected_router="agentic",
        expected_coordinator="recommendation",
        description="Consulta sobre optimización"
    ),
    
    # MULTI_AGENT
    TestCase(
        query="analiza la campaña de Baqueira",
        expected_router="multi_agent",
        expected_coordinator="multi",
        description="Análisis completo"
    ),
    TestCase(
        query="¿cómo está Costa del Sol?",
        expected_router="multi_agent",
        expected_coordinator="multi",
        description="Análisis ambiguo → multi"
    ),
]

# 🔄 Testing Contextual (Continuaciones)
CONTEXTUAL_TEST_CASES = [
    TestCase(
        query="baqueira",
        expected_router="agentic",
        expected_coordinator="performance",
        description="🔄 Continuación: Respuesta a pregunta del bot",
        context=[
            AIMessage(content="¿De qué campaña quieres ver las métricas?")
        ]
    ),
    TestCase(
        query="todas",
        expected_router="agentic",
        expected_coordinator="performance",
        description="🔄 Continuación: 'todas' en contexto",
        context=[
            AIMessage(content="¿Qué campaña quieres analizar?")
        ]
    ),
    TestCase(
        query="de la de ibiza",
        expected_router="agentic",
        expected_coordinator="config",
        description="🔄 Continuación: Referencia implícita",
        context=[
            HumanMessage(content="necesito el presupuesto"),
            AIMessage(content="¿De qué campaña necesitas el presupuesto?")
        ]
    ),
]

# ConfigAgent: Herramientas de configuración
CONFIG_AGENT_TEST_CASES = [
    TestCase(
        query="lista todas las campañas activas",
        should_use_tool="ListarCampanasInput",
        description="Listar campañas"
    ),
    TestCase(
        query="busca la campaña de Baqueira",
        should_use_tool="BuscarCampanaPorNombreInput",
        description="Buscar por nombre"
    ),
    TestCase(
        query="presupuesto de Costa Blanca",
        should_use_tool="ObtenerPresupuestoInput",
        description="Presupuesto específico (más rápido)"
    ),
    TestCase(
        query="dame todos los detalles de Menorca",
        should_use_tool="ObtenerDetallesCampanaInput",
        description="Detalles completos"
    ),
]

# PerformanceAgent: Métricas de rendimiento
PERFORMANCE_AGENT_TEST_CASES = [
    TestCase(
        query="gasto de Baqueira esta semana",
        should_use_tool="ObtenerMetricasCampanaInput",
        description="Métricas de campaña"
    ),
    TestCase(
        query="TOP 5 anuncios de Ibiza",
        should_use_tool="ObtenerAnunciosPorRendimientoInput",
        description="Top anuncios"
    ),
    TestCase(
        query="compara Baqueira vs semana pasada",
        should_use_tool="CompararPeriodosInput",
        description="Comparación de períodos"
    ),
    TestCase(
        query="CPA global de todas las campañas",
        should_use_tool="ObtenerCPAGlobalInput",
        description="Métricas globales"
    ),
]

# RecommendationAgent: Optimizaciones
RECOMMENDATION_AGENT_TEST_CASES = [
    TestCase(
        query="recomienda mejoras para Baqueira",
        should_use_tool="ObtenerRecomendacionesInput",
        description="Recomendaciones específicas"
    ),
    TestCase(
        query="analiza oportunidades de Advantage+ en todas las campañas",
        should_use_tool="ObtenerRecomendacionesInput",
        description="Análisis global"
    ),
]

# 🚨 Casos Edge (Queries problemáticas)
EDGE_CASES = [
    TestCase(
        query="¿Cómo fueron todas las campañas?",
        expected_router="agentic",
        expected_coordinator="performance",
        should_use_tool="CompararAnunciosGlobalesInput",
        description="🚨 EDGE: 'todas' sin especificar → NO preguntar"
    ),
    TestCase(
        query="dame todos los anuncios",
        expected_router="agentic",
        expected_coordinator="performance",
        should_use_tool="ObtenerAnunciosPorRendimientoInput",
        description="🚨 EDGE: 'todos' → limite=100, NO preguntar"
    ),
    TestCase(
        query="¿hay anuncios que hayan empeorado?",
        expected_router="agentic",
        expected_coordinator="performance",
        should_use_tool="CompararAnunciosInput",
        description="🚨 EDGE: Pregunta sin campaña específica"
    ),
]


# ========== FUNCIONES DE TESTING ==========

class TestRunner:
    """Ejecutor de tests con reportes detallados"""
    
    def __init__(self):
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "details": []
        }
        self.start_time = datetime.now()
    
    def run_router_tests(self, test_cases: List[TestCase]) -> None:
        """Testea Router V4"""
        print("\n" + "="*70)
        print("🔀 TESTING ROUTER V4")
        print("="*70)
        
        for test in test_cases:
            self.results["total"] += 1
            
            try:
                result = router_v4.classify(test.query, messages=test.context)
                
                passed = result.category == test.expected_router
                
                if passed:
                    self.results["passed"] += 1
                    status = "✅ PASS"
                else:
                    self.results["failed"] += 1
                    status = "❌ FAIL"
                
                detail = {
                    "test": test.description or test.query[:50],
                    "query": test.query,
                    "expected": test.expected_router,
                    "got": result.category,
                    "confidence": result.confidence,
                    "passed": passed
                }
                
                self.results["details"].append(detail)
                
                print(f"\n{status} | {test.description or test.query[:50]}")
                print(f"   Query: '{test.query}'")
                print(f"   Expected: {test.expected_router} | Got: {result.category} (conf: {result.confidence:.2f})")
                
                if not passed:
                    print(f"   ⚠️  Reasoning: {result.reasoning}")
            
            except Exception as e:
                self.results["errors"] += 1
                print(f"\n❌ ERROR | {test.description}")
                print(f"   Exception: {str(e)}")
    
    def run_coordinator_tests(self, test_cases: List[TestCase]) -> None:
        """Testea Coordinator"""
        print("\n" + "="*70)
        print("🎯 TESTING COORDINATOR")
        print("="*70)
        
        for test in test_cases:
            if not test.expected_coordinator:
                continue
            
            self.results["total"] += 1
            
            try:
                decision = coordinator.route(test.query)
                
                passed = decision.agent == test.expected_coordinator
                
                if passed:
                    self.results["passed"] += 1
                    status = "✅ PASS"
                else:
                    self.results["failed"] += 1
                    status = "❌ FAIL"
                
                print(f"\n{status} | {test.description or test.query[:50]}")
                print(f"   Query: '{test.query}'")
                print(f"   Expected: {test.expected_coordinator} | Got: {decision.agent} (conf: {decision.confidence:.2f})")
                
                if not passed:
                    print(f"   ⚠️  Reasoning: {decision.reasoning}")
            
            except Exception as e:
                self.results["errors"] += 1
                print(f"\n❌ ERROR | {test.description}")
                print(f"   Exception: {str(e)}")
    
    def run_agent_tool_tests(self, agent, agent_name: str, test_cases: List[TestCase]) -> None:
        """Testea herramientas de un agente específico"""
        print("\n" + "="*70)
        print(f"🤖 TESTING {agent_name.upper()}")
        print("="*70)
        
        for test in test_cases:
            self.results["total"] += 1
            
            try:
                config = {"configurable": {"thread_id": f"test_{agent_name}_{self.results['total']}"}}
                
                result = agent.invoke(
                    {"messages": [HumanMessage(content=test.query)]},
                    config=config
                )
                
                # Verificar si usó la herramienta esperada
                tool_calls = []
                for msg in result["messages"]:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_calls.extend([tc.name if hasattr(tc, 'name') else tc.get('name') for tc in msg.tool_calls])
                
                if test.should_use_tool:
                    passed = test.should_use_tool in tool_calls
                else:
                    passed = True  # Si no especifica tool, solo verifica que no haya error
                
                if passed:
                    self.results["passed"] += 1
                    status = "✅ PASS"
                else:
                    self.results["failed"] += 1
                    status = "❌ FAIL"
                
                print(f"\n{status} | {test.description or test.query[:50]}")
                print(f"   Query: '{test.query}'")
                if test.should_use_tool:
                    print(f"   Expected Tool: {test.should_use_tool}")
                    print(f"   Tools Used: {tool_calls}")
                
                final_msg = result["messages"][-1]
                if hasattr(final_msg, 'content'):
                    print(f"   Response (preview): {final_msg.content[:100]}...")
            
            except Exception as e:
                self.results["errors"] += 1
                print(f"\n❌ ERROR | {test.description}")
                print(f"   Exception: {str(e)}")
    
    def run_orchestrator_tests(self, test_cases: List[TestCase]) -> None:
        """Testea Orchestrator V5 end-to-end"""
        print("\n" + "="*70)
        print("🚀 TESTING ORCHESTRATOR V5 (End-to-End)")
        print("="*70)
        
        for test in test_cases:
            self.results["total"] += 1
            
            try:
                result = orchestrator_v5.process_query(test.query)
                
                # Validar workflow type
                if test.expected_router:
                    if test.expected_router == "simple":
                        expected_workflow = "simple"
                    elif test.expected_router == "agentic":
                        if test.expected_coordinator:
                            expected_workflow = f"agentic_{test.expected_coordinator}"
                        else:
                            expected_workflow = "agentic"
                    elif test.expected_router == "multi_agent":
                        expected_workflow = "multi_agent"
                    else:
                        expected_workflow = test.expected_router
                    
                    passed = (
                        result.workflow_type == expected_workflow or
                        result.workflow_type.startswith(expected_workflow.split('_')[0])
                    )
                else:
                    passed = result.content and len(result.content) > 0
                
                if passed:
                    self.results["passed"] += 1
                    status = "✅ PASS"
                else:
                    self.results["failed"] += 1
                    status = "❌ FAIL"
                
                print(f"\n{status} | {test.description or test.query[:50]}")
                print(f"   Query: '{test.query}'")
                if test.expected_router:
                    print(f"   Expected Workflow: {expected_workflow}")
                print(f"   Got Workflow: {result.workflow_type}")
                print(f"   Response (preview): {result.content[:150]}...")
            
            except Exception as e:
                self.results["errors"] += 1
                print(f"\n❌ ERROR | {test.description}")
                print(f"   Exception: {str(e)}")
    
    def print_summary(self) -> None:
        """Imprime resumen final"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "="*70)
        print("📊 RESUMEN DE TESTS")
        print("="*70)
        print(f"\n⏱️  Tiempo total: {elapsed:.2f}s")
        print(f"\n📋 Tests ejecutados: {self.results['total']}")
        print(f"   ✅ Passed: {self.results['passed']}")
        print(f"   ❌ Failed: {self.results['failed']}")
        print(f"   ⚠️  Errors: {self.results['errors']}")
        
        success_rate = (self.results['passed'] / self.results['total'] * 100) if self.results['total'] > 0 else 0
        print(f"\n🎯 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        elif success_rate >= 90:
            print("\n✅ Tests mayormente exitosos")
        elif success_rate >= 70:
            print("\n⚠️  Algunos tests fallaron - revisar")
        else:
            print("\n❌ Muchos tests fallaron - requiere atención urgente")
        
        # Detalles de fallos
        failed_tests = [d for d in self.results["details"] if not d.get("passed", True)]
        if failed_tests:
            print("\n" + "="*70)
            print("❌ TESTS FALLIDOS:")
            print("="*70)
            for test in failed_tests:
                print(f"\n🔸 {test['test']}")
                print(f"   Query: {test['query']}")
                print(f"   Expected: {test['expected']} | Got: {test['got']}")
        
        print("\n" + "="*70)


# ========== QUERIES HABITUALES SUGERIDAS ==========

QUERIES_HABITUALES = """
📋 QUERIES HABITUALES QUE USUARIOS REALES HARÍAN:

🔍 Exploración General:
- "¿Qué campañas tengo activas?"
- "Dame un resumen de todas mis campañas"
- "¿Cómo van las campañas en general?"

💰 Configuración:
- "¿Cuál es el presupuesto de Baqueira?"
- "¿Qué estrategia de puja tiene Ibiza?"
- "Lista todas las campañas pausadas"
- "¿Está activado Advantage+ en Costa Blanca?"

📊 Rendimiento:
- "¿Cuánto he gastado esta semana?"
- "¿Cuántas conversiones tuve ayer?"
- "Dame el CPA de todas las campañas"
- "¿Qué destino tiene mejor ROI?"
- "Compara esta semana vs la anterior"

🎯 Anuncios (NUEVA FUNCIONALIDAD):
- "¿Qué anuncios tienen mejor CTR?"
- "¿Hay algún anuncio que haya empeorado?"
- "Dame todos los anuncios de Baqueira"
- "¿Qué anuncio explica el aumento del CPA?"
- "TOP 5 anuncios con más conversiones"
- "¿Cuál es el peor anuncio de Ibiza?"

💡 Optimización:
- "¿Qué puedo optimizar en mis campañas?"
- "Dame recomendaciones para reducir el CPA"
- "¿Debería subir el presupuesto de Baqueira?"
- "¿Por qué el CPA de Ibiza es tan alto?"

📈 Análisis Completo:
- "Analiza la campaña de Baqueira"
- "¿Cómo está Costa del Sol en general?"
- "Dame un reporte completo de Menorca"
- "Analiza rendimiento + dame sugerencias de Ibiza"

🔄 Conversacionales (Continuaciones):
Usuario: "¿Cómo están las campañas?"
Bot: "¿De qué campaña específica?"
Usuario: "Baqueira" ← debe continuar sin preguntar de nuevo

Usuario: "¿Hay anuncios con mal rendimiento?"
Bot: "¿De qué campaña?"
Usuario: "todas" ← debe analizar TODAS sin preguntar

🚨 Casos Problemáticos (Edge Cases):
- "dame todos" ← ¿todos qué? (anuncios/campañas/destinos)
- "cómo fue la semana pasada" ← ¿de qué?
- "mejora esto" ← sin contexto previo
- "qué anuncio" ← pregunta incompleta

🎯 Queries Multilenguaje:
- "show me all campaigns"
- "¿cuánto spent en Baqueira?"
- "dame el top 3 ads"
"""


# ========== MAIN ==========

def main():
    """Ejecuta suite completa de tests"""
    print("\n" + "="*70)
    print("🧪 META ADS AGENT V5 - SUITE COMPLETA DE TESTING")
    print("="*70)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    runner = TestRunner()
    
    # 1. Router V4
    runner.run_router_tests(ROUTER_TEST_CASES)
    runner.run_router_tests(CONTEXTUAL_TEST_CASES)
    runner.run_router_tests(ANUNCIOS_TEST_CASES)
    runner.run_router_tests(EDGE_CASES)
    
    # 2. Coordinator
    runner.run_coordinator_tests(ROUTER_TEST_CASES)
    runner.run_coordinator_tests(ANUNCIOS_TEST_CASES)
    
    # 3. Agentes Individuales
    runner.run_agent_tool_tests(config_agent, "ConfigAgent", CONFIG_AGENT_TEST_CASES)
    runner.run_agent_tool_tests(performance_agent, "PerformanceAgent", PERFORMANCE_AGENT_TEST_CASES)
    runner.run_agent_tool_tests(performance_agent, "PerformanceAgent (Anuncios)", ANUNCIOS_TEST_CASES)
    runner.run_agent_tool_tests(recommendation_agent, "RecommendationAgent", RECOMMENDATION_AGENT_TEST_CASES)
    
    # 4. Orchestrator End-to-End
    runner.run_orchestrator_tests(ROUTER_TEST_CASES[:5])  # Subset para no saturar
    runner.run_orchestrator_tests(ANUNCIOS_TEST_CASES[:3])
    runner.run_orchestrator_tests(EDGE_CASES)
    
    # 5. Resumen Final
    runner.print_summary()
    
    # 6. Imprimir queries habituales
    print(QUERIES_HABITUALES)
    
    # 7. Guardar reporte
    report_path = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(runner.results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Reporte guardado en: {report_path}")
    
    # Retornar código de salida
    sys.exit(0 if runner.results["failed"] == 0 and runner.results["errors"] == 0 else 1)


if __name__ == "__main__":
    main()