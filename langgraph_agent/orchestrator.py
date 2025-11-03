"""
Orchestrator - Día 1
Integra Router + Fast Path + Agentic Workflow

USO:
    from orchestrator import Orchestrator
    
    orchestrator = Orchestrator()
    response = orchestrator.process_query("lista todas las campañas", thread_id="user123")
    print(response)
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Importar módulos locales
from router import QueryRouter
from workflows import FastPathWorkflow, AgenticWorkflow, WorkflowResult

# Importar el agente compilado
from agent import app as agent_app

load_dotenv()


class Orchestrator:
    """
    Orquestador principal que integra:
    - Router (clasificación)
    - Fast Path Workflow (consultas simples)
    - Agentic Workflow (consultas complejas)
    """
    
    def __init__(self):
        """Inicializa el orchestrator con todos los componentes."""
        
        print("🚀 Inicializando Orchestrator...")
        
        # 1. Router
        self.router = QueryRouter()
        print("   ✅ Router inicializado")
        
        # 2. Fast Path Workflow
        langserve_url = os.getenv("TOOL_SERVER_BASE_URL", "http://localhost:8000")
        api_key = os.getenv("TOOL_API_KEY", "53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG")
        
        self.fast_path = FastPathWorkflow(
            langserve_url=langserve_url,
            api_key=api_key
        )
        print("   ✅ Fast Path Workflow inicializado")
        
        # 3. Agentic Workflow (usa el agente actual)
        self.agentic = AgenticWorkflow(agent_app)
        print("   ✅ Agentic Workflow inicializado")
        
        print("✅ Orchestrator listo\n")
    
    def process_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        force_workflow: Optional[str] = None
    ) -> WorkflowResult:
        """
        Procesa una consulta del usuario.
        
        Args:
            query: La consulta del usuario
            thread_id: ID del thread para memoria (opcional, se genera automáticamente)
            force_workflow: Forzar un workflow específico ("simple" o "complejo")
                           útil para debugging
        
        Returns:
            WorkflowResult con la respuesta
        """
        
        # Generar thread_id si no se proporciona
        if not thread_id:
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*70)
        print(f"📥 NUEVA CONSULTA")
        print(f"   User Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        try:
            # PASO 1: Clasificar la consulta (a menos que se fuerce un workflow)
            if force_workflow:
                category = force_workflow
                print(f"\n⚠️  FORZANDO WORKFLOW: {category.upper()}")
            else:
                route_result = self.router.classify(query)
                category = route_result.category
            
            # PASO 2: Ejecutar el workflow correspondiente
            if category == "simple":
                result = self.fast_path.execute(query)
            
            elif category == "complejo":
                result = self.agentic.execute(query, thread_id)
            
            else:
                # Fallback (no debería ocurrir)
                result = WorkflowResult(
                    content=f"❌ Categoría desconocida: {category}",
                    workflow_type="error",
                    metadata={"error": "unknown_category"}
                )
            
            # PASO 3: Logging final
            print("\n" + "="*70)
            print(f"✅ RESPUESTA GENERADA")
            print(f"   Workflow: {result.workflow_type.upper()}")
            print(f"   Metadata: {result.metadata}")
            print("="*70 + "\n")
            
            return result
        
        except Exception as e:
            print(f"\n❌ ERROR EN ORCHESTRATOR: {e}")
            
            return WorkflowResult(
                content=f"❌ Error inesperado: {str(e)}",
                workflow_type="error",
                metadata={"error": str(e)}
            )
    
    def chat(self, thread_id: Optional[str] = None):
        """
        Modo interactivo de chat.
        
        Args:
            thread_id: ID del thread para mantener la conversación
        """
        
        if not thread_id:
            thread_id = f"interactive_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*70)
        print("💬 MODO CHAT INTERACTIVO")
        print(f"   Thread ID: {thread_id}")
        print("   Comandos especiales:")
        print("     - 'salir' o 'exit' para terminar")
        print("     - 'nuevo' para nuevo thread")
        print("="*70 + "\n")
        
        while True:
            try:
                user_input = input("👤 Tú: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['salir', 'exit', 'quit']:
                    print("\n👋 ¡Hasta luego!")
                    break
                
                if user_input.lower() == 'nuevo':
                    thread_id = f"interactive_{uuid.uuid4().hex[:8]}"
                    print(f"\n🔄 Nuevo thread iniciado: {thread_id}\n")
                    continue
                
                # Procesar la consulta
                result = self.process_query(user_input, thread_id=thread_id)
                
                # Mostrar respuesta
                print(f"\n🤖 Agente:\n{result.content}\n")
                print("-"*70 + "\n")
            
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrumpido. ¡Hasta luego!")
                break
            
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


# Script de prueba
def run_day1_tests():
    """Script de validación para Día 1."""
    
    print("\n" + "🧪"*35)
    print("PRUEBAS DE VALIDACIÓN - DÍA 1")
    print("🧪"*35 + "\n")
    
    orchestrator = Orchestrator()
    
    # Test 1: Consultas SIMPLES (Fast Path)
    print("\n📋 TEST 1: CONSULTAS SIMPLES")
    print("-"*70)
    
    simple_queries = [
        "lista todas las campañas",
        "muéstrame las campañas activas",
        "¿cuántas campañas tengo?",
    ]
    
    for query in simple_queries:
        result = orchestrator.process_query(query)
        print(f"✓ Query: '{query}'")
        print(f"  Workflow: {result.workflow_type}")
        print()
    
    # Test 2: Consultas COMPLEJAS (Agentic)
    print("\n📊 TEST 2: CONSULTAS COMPLEJAS")
    print("-"*70)
    
    thread_id = "test_complex"
    
    complex_queries = [
        "dame el TOP 3 de anuncios de Baqueira del último mes",
        "¿cuál tiene mejor CPA?",
    ]
    
    for query in complex_queries:
        result = orchestrator.process_query(query, thread_id=thread_id)
        print(f"✓ Query: '{query}'")
        print(f"  Workflow: {result.workflow_type}")
        print(f"  Tools: {result.metadata.get('tools_used', 'N/A')}")
        print()
    
    print("\n" + "✅"*35)
    print("VALIDACIÓN COMPLETA")
    print("✅"*35 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Ejecutar tests de validación
        run_day1_tests()
    
    elif len(sys.argv) > 1 and sys.argv[1] == "chat":
        # Modo interactivo
        orchestrator = Orchestrator()
        orchestrator.chat()
    
    else:
        # Demo rápido
        orchestrator = Orchestrator()
        
        print("\n📝 DEMO RÁPIDO:")
        print("-"*70)
        
        # Consulta simple
        result1 = orchestrator.process_query("lista todas las campañas")
        print(f"Resultado:\n{result1.content}\n")
        
        # Consulta compleja
        result2 = orchestrator.process_query(
            "dame el TOP 3 de anuncios de Baqueira",
            thread_id="demo_thread"
        )
        print(f"Resultado:\n{result2.content}\n")