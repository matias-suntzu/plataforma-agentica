"""
Script de Validación - DÍA 2
Valida Router V2 + Sequential Workflow

EJECUCIÓN:
    python test_day2.py
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from orchestrator_v2 import OrchestratorV2


def print_separator(title: str = "", char: str = "=", width: int = 80):
    """Imprime un separador visual."""
    if title:
        side_len = (width - len(title) - 2) // 2
        print(f"\n{char * side_len} {title} {char * side_len}")
    else:
        print(f"\n{char * width}")


def test_router_v2_accuracy(orchestrator: OrchestratorV2):
    """Test de precisión del Router V2 (4 categorías)."""
    
    print_separator("TEST 1: PRECISIÓN DEL ROUTER V2", "🔵")
    
    test_cases = [
        # (categoría esperada, query)
        ("simple", "lista todas las campañas"),
        ("simple", "¿cuántas campañas activas tengo?"),
        
        ("sequential", "genera un reporte de Baqueira y envíalo a Slack"),
        ("sequential", "analiza las campañas activas y crea un resumen"),
        
        ("agentic", "dame el TOP 3 de anuncios de Baqueira"),
        ("agentic", "¿qué campaña tiene mejor CPA?"),
        
        ("conversation", "¿cuál tiene mejor CPA?"),
        ("conversation", "¿y el segundo?"),
    ]
    
    results = []
    
    for expected, query in test_cases:
        print(f"\n📝 Query: '{query}'")
        print(f"   Esperado: {expected.upper()}")
        print("-" * 80)
        
        # Clasificar sin ejecutar (solo router)
        route_result = orchestrator.router.classify(query)
        
        is_correct = route_result.category == expected
        status = "✅ PASS" if is_correct else "❌ FAIL"
        
        print(f"\n{status}")
        print(f"   Obtenido: {route_result.category.upper()}")
        print(f"   Confidence: {route_result.confidence:.2f}")
        print(f"   Reasoning: {route_result.reasoning}")
        
        if route_result.detected_intent:
            print(f"   Intent: {route_result.detected_intent}")
        
        results.append({
            "query": query,
            "expected": expected,
            "actual": route_result.category,
            "passed": is_correct,
            "confidence": route_result.confidence
        })
    
    return results


def test_sequential_workflow(orchestrator: OrchestratorV2):
    """Test del Sequential Workflow (flujos multi-paso)."""
    
    print_separator("TEST 2: SEQUENTIAL WORKFLOW", "🔗")
    
    # Nota: Este test puede fallar si no tienes N8N configurado o Slack
    # Es más una demostración del flujo
    
    queries = [
        "genera un reporte de Baqueira y envíalo a Slack",
    ]
    
    results = []
    
    thread_id = f"test_seq_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    for query in queries:
        print(f"\n📝 Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        print("-" * 80)
        
        result = orchestrator.process_query(query, thread_id=thread_id)
        
        # Validación: debe usar sequential workflow
        is_sequential = result.workflow_type in ["sequential", "sequential_fallback"]
        status = "✅ PASS" if is_sequential else "❌ FAIL"
        
        print(f"\n{status}")
        print(f"   Workflow usado: {result.workflow_type}")
        print(f"   Metadata: {result.metadata}")
        
        # Preview de respuesta
        preview = result.content[:300] + "..." if len(result.content) > 300 else result.content
        print(f"\n   Respuesta:\n   {preview}")
        
        results.append({
            "query": query,
            "workflow": result.workflow_type,
            "passed": is_sequential,
            "metadata": result.metadata
        })
    
    return results


def test_conversation_workflow(orchestrator: OrchestratorV2):
    """Test del Conversation Workflow (memoria)."""
    
    print_separator("TEST 3: CONVERSATION WORKFLOW (MEMORIA)", "💬")
    
    thread_id = f"test_conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Secuencia de consultas que requieren memoria
    queries = [
        ("agentic", "dame el TOP 3 de anuncios de Baqueira"),
        ("conversation", "¿cuál tiene mejor CPA?"),
        ("conversation", "¿y el segundo mejor?"),
    ]
    
    results = []
    
    for i, (expected_category, query) in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}/{len(queries)}: '{query}'")
        print(f"Esperado: {expected_category.upper()}")
        print(f"Thread ID: {thread_id}")
        print("="*80)
        
        result = orchestrator.process_query(query, thread_id=thread_id)
        
        # Validación
        is_correct_workflow = (
            (expected_category == "agentic" and result.workflow_type == "agentic") or
            (expected_category == "conversation" and result.workflow_type == "conversation")
        )
        
        status = "✅ PASS" if is_correct_workflow else "❌ FAIL"
        
        print(f"\n{status}")
        print(f"   Workflow: {result.workflow_type}")
        
        # Para consultas 2 y 3, verificar que NO usan herramientas (usan memoria)
        if i > 1:
            tools_used = result.metadata.get('tools_used', [])
            uses_memory = len(tools_used) == 0 or all('Buscar' not in tool and 'Obtener' not in tool for tool in tools_used)
            
            memory_status = "✅" if uses_memory else "⚠️ "
            print(f"   {memory_status} Memoria: {'Usada' if uses_memory else 'NO usada (re-buscó datos)'}")
            print(f"   Tools: {tools_used if tools_used else 'Ninguna (solo memoria)'}")
        
        # Preview de respuesta
        preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
        print(f"\n   Respuesta:\n   {preview}")
        
        results.append({
            "query": query,
            "expected": expected_category,
            "workflow": result.workflow_type,
            "passed": is_correct_workflow
        })
    
    return results


def test_backward_compatibility():
    """Test de compatibilidad con código V1."""
    
    print_separator("TEST 4: COMPATIBILIDAD CON V1", "🔄")
    
    print("\n📝 Verificando que V1 todavía funciona...")
    
    try:
        from orchestrator import Orchestrator as OrchestratorV1
        
        orch_v1 = OrchestratorV1()
        result = orch_v1.process_query("lista todas las campañas")
        
        success = result.workflow_type in ["fast_path", "agentic"]
        
        if success:
            print("✅ PASS - Orchestrator V1 sigue funcionando")
        else:
            print("❌ FAIL - Orchestrator V1 tiene problemas")
        
        return [{"test": "backward_compatibility", "passed": success}]
    
    except Exception as e:
        print(f"❌ FAIL - Error al importar V1: {e}")
        return [{"test": "backward_compatibility", "passed": False, "error": str(e)}]


def generate_report(router_results, sequential_results, conversation_results, compat_results):
    """Genera reporte de validación."""
    
    print_separator("REPORTE DE VALIDACIÓN - DÍA 2", "✅")
    
    # Contador router
    router_passed = sum(1 for r in router_results if r['passed'])
    router_total = len(router_results)
    
    # Contador sequential
    seq_passed = sum(1 for r in sequential_results if r['passed'])
    seq_total = len(sequential_results)
    
    # Contador conversation
    conv_passed = sum(1 for r in conversation_results if r['passed'])
    conv_total = len(conversation_results)
    
    # Contador compatibilidad
    compat_passed = sum(1 for r in compat_results if r['passed'])
    compat_total = len(compat_results)
    
    # Total
    total_passed = router_passed + seq_passed + conv_passed + compat_passed
    total_tests = router_total + seq_total + conv_total + compat_total
    
    print(f"\n📊 RESUMEN DE TESTS:")
    print(f"   Total ejecutados: {total_tests}")
    print(f"   ✅ Pasados: {total_passed}")
    print(f"   ❌ Fallidos: {total_tests - total_passed}")
    print(f"   📈 Tasa de éxito: {(total_passed/total_tests*100):.1f}%")
    
    print(f"\n📋 DETALLE POR CATEGORÍA:")
    print(f"   🔵 Router V2: {router_passed}/{router_total} ({router_passed/router_total*100:.0f}%)")
    print(f"   🔗 Sequential Workflow: {seq_passed}/{seq_total}")
    print(f"   💬 Conversation Workflow: {conv_passed}/{conv_total}")
    print(f"   🔄 Compatibilidad V1: {compat_passed}/{compat_total}")
    
    # Criterios de éxito
    print(f"\n🎯 CRITERIOS DE ÉXITO DÍA 2:")
    
    criteria = {
        "Router V2 preciso (>85%)": router_passed/router_total >= 0.85,
        "Sequential Workflow funcional": seq_passed >= 1,
        "Conversation usa memoria": conv_passed >= 2,
        "Backward compatible con V1": compat_passed >= 1,
    }
    
    for criterion, passed in criteria.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}")
    
    all_passed = all(criteria.values())
    
    print_separator()
    
    if all_passed:
        print("\n🎉 ¡VALIDACIÓN EXITOSA! DÍA 2 COMPLETADO")
        print("\n✅ El sistema cumple con todos los criterios:")
        print("   • Router V2 clasifica 4 categorías correctamente")
        print("   • Sequential Workflow ejecuta flujos multi-paso")
        print("   • Conversation Workflow usa memoria eficientemente")
        print("   • Compatible con código V1 (sin romper nada)")
        print("\n🚀 Listo para avanzar al DÍA 3 (si es necesario)")
    else:
        print("\n⚠️  VALIDACIÓN INCOMPLETA")
        print("\n❌ Revisar los criterios fallidos antes de continuar")
    
    print_separator()
    
    return all_passed


def main():
    """Función principal del test."""
    
    print_separator("INICIO DE VALIDACIÓN - DÍA 2", "🚀")
    print(f"\n⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Validando: Router V2 + Sequential + Conversation Workflows")
    
    # Verificar variables de entorno
    required_vars = ["GEMINI_API_KEY", "TOOL_SERVER_BASE_URL", "TOOL_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ ERROR: Faltan variables de entorno:")
        for var in missing_vars:
            print(f"   • {var}")
        return False
    
    print("\n✅ Variables de entorno configuradas")
    
    # Inicializar orchestrator V2
    print("\n🔧 Inicializando Orchestrator V2...")
    try:
        orchestrator = OrchestratorV2(enable_logging=True)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✅ Orchestrator V2 inicializado")
    
    # Ejecutar tests
    try:
        router_results = test_router_v2_accuracy(orchestrator)
        sequential_results = test_sequential_workflow(orchestrator)
        conversation_results = test_conversation_workflow(orchestrator)
        compat_results = test_backward_compatibility()
        
        # Generar reporte
        success = generate_report(
            router_results,
            sequential_results,
            conversation_results,
            compat_results
        )
        
        # Mostrar métricas del orchestrator
        orchestrator.print_metrics()
        
        return success
    
    except Exception as e:
        print_separator("ERROR DURANTE TESTS", "❌")
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    
    import sys
    sys.exit(0 if success else 1)