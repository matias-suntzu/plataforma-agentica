"""
Script de Validación - DÍA 1
Valida que el Router + Workflows funcionan correctamente

EJECUCIÓN:
    python test_day1.py
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Importar el orchestrator
from orchestrator import Orchestrator


def print_separator(title: str = "", char: str = "=", width: int = 80):
    """Imprime un separador visual."""
    if title:
        side_len = (width - len(title) - 2) // 2
        print(f"\n{char * side_len} {title} {char * side_len}")
    else:
        print(f"\n{char * width}")


def test_simple_queries(orchestrator: Orchestrator):
    """Test de consultas SIMPLES (Fast Path)."""
    
    print_separator("TEST 1: CONSULTAS SIMPLES (FAST PATH)", "🔵")
    
    queries = [
        ("Lista todas las campañas", "lista todas las campañas"),
        ("Campañas activas", "muéstrame las campañas activas"),
        ("Contador de campañas", "¿cuántas campañas tengo?"),
    ]
    
    results = []
    
    for name, query in queries:
        print(f"\n📝 {name}")
        print(f"   Query: '{query}'")
        print("-" * 80)
        
        result = orchestrator.process_query(query)
        
        # Validación
        is_fast_path = result.workflow_type == "fast_path"
        status = "✅ PASS" if is_fast_path else "❌ FAIL"
        
        print(f"\n{status}")
        print(f"   Workflow usado: {result.workflow_type}")
        print(f"   Metadata: {result.metadata}")
        
        results.append({
            "name": name,
            "query": query,
            "passed": is_fast_path,
            "workflow": result.workflow_type
        })
        
        if len(result.content) > 500:
            print(f"\n   Respuesta (preview):\n   {result.content[:500]}...")
        else:
            print(f"\n   Respuesta:\n   {result.content}")
    
    return results


def test_complex_queries(orchestrator: Orchestrator):
    """Test de consultas COMPLEJAS (Agentic)."""
    
    print_separator("TEST 2: CONSULTAS COMPLEJAS (AGENTIC WORKFLOW)", "🔴")
    
    thread_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    queries = [
        ("TOP 3 con análisis", "dame el TOP 3 de anuncios de Baqueira del último mes"),
        ("Pregunta de seguimiento", "¿cuál tiene mejor CPA?"),
        ("Comparación de períodos", "compara este mes vs el mes pasado"),
    ]
    
    results = []
    
    for name, query in queries:
        print(f"\n📝 {name}")
        print(f"   Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        print("-" * 80)
        
        result = orchestrator.process_query(query, thread_id=thread_id)
        
        # Validación
        is_agentic = result.workflow_type == "agentic"
        status = "✅ PASS" if is_agentic else "❌ FAIL"
        
        print(f"\n{status}")
        print(f"   Workflow usado: {result.workflow_type}")
        print(f"   Herramientas: {result.metadata.get('tools_used', 'Ninguna')}")
        print(f"   Metadata: {result.metadata}")
        
        results.append({
            "name": name,
            "query": query,
            "passed": is_agentic,
            "workflow": result.workflow_type,
            "tools": result.metadata.get('tools_used', [])
        })
        
        if len(result.content) > 500:
            print(f"\n   Respuesta (preview):\n   {result.content[:500]}...")
        else:
            print(f"\n   Respuesta:\n   {result.content}")
    
    return results


def test_edge_cases(orchestrator: Orchestrator):
    """Test de casos límite y ambiguos."""
    
    print_separator("TEST 3: CASOS LÍMITE Y AMBIGUOS", "🟡")
    
    queries = [
        ("Pregunta fuera de contexto", "¿cuál es el clima hoy?"),
        ("Pregunta ambigua", "dime sobre las campañas"),
    ]
    
    results = []
    
    for name, query in queries:
        print(f"\n📝 {name}")
        print(f"   Query: '{query}'")
        print("-" * 80)
        
        result = orchestrator.process_query(query)
        
        print(f"\n   Workflow usado: {result.workflow_type}")
        print(f"   Metadata: {result.metadata}")
        
        results.append({
            "name": name,
            "query": query,
            "workflow": result.workflow_type
        })
        
        if len(result.content) > 300:
            print(f"\n   Respuesta (preview):\n   {result.content[:300]}...")
        else:
            print(f"\n   Respuesta:\n   {result.content}")
    
    return results


def generate_report(simple_results, complex_results, edge_results):
    """Genera un reporte de validación."""
    
    print_separator("REPORTE DE VALIDACIÓN - DÍA 1", "✅")
    
    # Contador de resultados
    simple_passed = sum(1 for r in simple_results if r['passed'])
    simple_total = len(simple_results)
    
    complex_passed = sum(1 for r in complex_results if r['passed'])
    complex_total = len(complex_results)
    
    total_passed = simple_passed + complex_passed
    total_tests = simple_total + complex_total
    
    print(f"\n📊 RESUMEN DE TESTS:")
    print(f"   Total ejecutados: {total_tests}")
    print(f"   ✅ Pasados: {total_passed}")
    print(f"   ❌ Fallidos: {total_tests - total_passed}")
    print(f"   📈 Tasa de éxito: {(total_passed/total_tests*100):.1f}%")
    
    print(f"\n📋 DETALLE POR CATEGORÍA:")
    print(f"   🔵 Consultas Simples: {simple_passed}/{simple_total}")
    print(f"   🔴 Consultas Complejas: {complex_passed}/{complex_total}")
    print(f"   🟡 Casos Límite: {len(edge_results)} ejecutados")
    
    # Verificar criterios de éxito del Día 1
    print(f"\n🎯 CRITERIOS DE ÉXITO DÍA 1:")
    
    criteria = {
        "Router funcional": simple_total > 0 and complex_total > 0,
        "Fast Path responde": simple_passed >= 2,
        "Agentic Workflow responde": complex_passed >= 1,
        "Integración completa": total_passed == total_tests,
    }
    
    for criterion, passed in criteria.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}")
    
    all_passed = all(criteria.values())
    
    print_separator()
    
    if all_passed:
        print("\n🎉 ¡VALIDACIÓN EXITOSA! DÍA 1 COMPLETADO")
        print("\n✅ El sistema cumple con todos los criterios:")
        print("   • Router clasifica correctamente")
        print("   • Fast Path responde consultas simples")
        print("   • Agentic Workflow maneja consultas complejas")
        print("   • Integración funciona end-to-end")
        print("\n🚀 Listo para avanzar al DÍA 2")
    else:
        print("\n⚠️  VALIDACIÓN INCOMPLETA")
        print("\n❌ Revisar los criterios fallidos antes de continuar")
    
    print_separator()
    
    return all_passed


def main():
    """Función principal del test."""
    
    print_separator("INICIO DE VALIDACIÓN - DÍA 1", "🚀")
    print(f"\n⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Validando: Router + Fast Path + Agentic Workflow")
    
    # Verificar variables de entorno
    required_vars = ["GEMINI_API_KEY", "TOOL_SERVER_BASE_URL", "TOOL_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ ERROR: Faltan variables de entorno:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\n💡 Configura estas variables en tu archivo .env")
        return False
    
    print("\n✅ Variables de entorno configuradas")
    
    # Inicializar orchestrator
    print("\n🔧 Inicializando Orchestrator...")
    try:
        orchestrator = Orchestrator()
    except Exception as e:
        print(f"\n❌ ERROR al inicializar Orchestrator: {e}")
        print("\n💡 Verifica que:")
        print("   • server.py esté corriendo (puerto 8000)")
        print("   • Las credenciales de Meta Ads sean correctas")
        print("   • agent.py no tenga errores de sintaxis")
        import traceback
        traceback.print_exc()
        return False
    
    print("✅ Orchestrator inicializado correctamente")
    
    # Ejecutar tests
    try:
        simple_results = test_simple_queries(orchestrator)
        complex_results = test_complex_queries(orchestrator)
        edge_results = test_edge_cases(orchestrator)
        
        # Generar reporte final
        success = generate_report(simple_results, complex_results, edge_results)
        
        return success
    
    except Exception as e:
        print_separator("ERROR DURANTE TESTS", "❌")
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    
    # Exit code para CI/CD
    import sys
    sys.exit(0 if success else 1)