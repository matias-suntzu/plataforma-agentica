"""
Orchestrator V2 - Día 2
Orchestrator mejorado con 4 workflows

MEJORAS vs V1:
- Soporta 4 tipos de workflow (simple, sequential, agentic, conversation)
- Logging estructurado a archivo
- Métricas de rendimiento por workflow
- Mejor manejo de thread IDs

USO:
    from orchestrator_v2 import OrchestratorV2
    
    orch = OrchestratorV2()
    result = orch.process_query("genera reporte de Baqueira y envíalo a Slack")
    print(result.content)
"""

import os
import uuid
import json
from datetime import datetime
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Importar router V2 y workflows V2
from router_v2 import QueryRouterV2
from workflows_v2 import (
    FastPathWorkflow,
    SequentialWorkflow,
    AgenticWorkflow,
    ConversationWorkflow,
    WorkflowResult
)

# Importar el agente compilado
from agent import app as agent_app

load_dotenv()


class OrchestratorV2:
    """
    Orchestrator mejorado con 4 workflows y logging avanzado.
    
    Workflows soportados:
    1. FastPath (simple) - Consultas básicas sin LLM
    2. Sequential (sequential) - Flujos multi-paso predefinidos
    3. Agentic (agentic) - Análisis complejos con razonamiento
    4. Conversation (conversation) - Preguntas de seguimiento con memoria
    """
    
    def __init__(self, enable_logging: bool = True):
        """
        Inicializa el orchestrator V2.
        
        Args:
            enable_logging: Si True, guarda logs en archivos JSONL
        """
        print("🚀 Inicializando Orchestrator V2...")
        
        # 1. Router V2
        self.router = QueryRouterV2(log_to_file=enable_logging)
        print("   ✅ Router V2 inicializado (4 categorías)")
        
        # 2. Configuración de herramientas
        langserve_url = os.getenv("TOOL_SERVER_BASE_URL", "http://localhost:8000")
        api_key = os.getenv("TOOL_API_KEY", "53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG")
        
        # 3. Inicializar workflows
        self.fast_path = FastPathWorkflow(langserve_url, api_key)
        self.sequential = SequentialWorkflow(langserve_url, api_key, agent_app)
        self.agentic = AgenticWorkflow(agent_app)
        self.conversation = ConversationWorkflow(agent_app)
        
        print("   ✅ Fast Path Workflow inicializado")
        print("   ✅ Sequential Workflow inicializado (NUEVO)")
        print("   ✅ Agentic Workflow inicializado")
        print("   ✅ Conversation Workflow inicializado (NUEVO)")
        
        # 4. Logging
        self.enable_logging = enable_logging
        self.log_file = "orchestrator_v2_metrics.jsonl"
        
        # 5. Métricas de rendimiento
        self.metrics = {
            "simple": {"count": 0, "total_time": 0},
            "sequential": {"count": 0, "total_time": 0},
            "agentic": {"count": 0, "total_time": 0},
            "conversation": {"count": 0, "total_time": 0}
        }
        
        print("✅ Orchestrator V2 listo\n")
    
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
            force_workflow: Forzar un workflow específico para debugging
                          Valores: "simple", "sequential", "agentic", "conversation"
        
        Returns:
            WorkflowResult con la respuesta y metadata
        
        Ejemplo:
            >>> orch = OrchestratorV2()
            >>> result = orch.process_query("lista todas las campañas")
            >>> print(result.content)
        """
        start_time = datetime.now()
        
        # Generar thread_id si no se proporciona
        if not thread_id:
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*70)
        print(f"📥 NUEVA CONSULTA")
        print(f"   User Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        print(f"   Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        try:
            # PASO 1: Clasificar la consulta (a menos que se fuerce un workflow)
            if force_workflow:
                category = force_workflow
                print(f"\n⚠️  FORZANDO WORKFLOW: {category.upper()}")
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
            
            else:
                # Fallback (no debería ocurrir)
                result = WorkflowResult(
                    content=f"❌ Categoría desconocida: {category}",
                    workflow_type="error",
                    metadata={"error": "unknown_category"}
                )
            
            # PASO 3: Calcular métricas
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            
            # Actualizar métricas internas
            if category in self.metrics:
                self.metrics[category]["count"] += 1
                self.metrics[category]["total_time"] += elapsed_time
            
            # PASO 4: Logging visual
            print("\n" + "="*70)
            print(f"✅ RESPUESTA GENERADA")
            print(f"   Workflow: {result.workflow_type.upper()}")
            print(f"   Tiempo: {elapsed_time:.2f}s")
            print(f"   Metadata: {result.metadata}")
            print("="*70 + "\n")
            
            # PASO 5: Guardar log a archivo
            if self.enable_logging:
                self._log_query(query, category, result, elapsed_time, route_result)
            
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
    
    def _log_query(
        self,
        query: str,
        category: str,
        result: WorkflowResult,
        elapsed_time: float,
        route_result
    ):
        """Guarda métricas de la consulta en archivo JSONL."""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "category": category,
            "workflow_type": result.workflow_type,
            "elapsed_time": elapsed_time,
            "router_confidence": route_result.confidence if route_result else None,
            "metadata": result.metadata
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️  Error al guardar log: {e}")
    
    def get_metrics(self) -> dict:
        """
        Retorna métricas agregadas del orchestrator.
        
        Returns:
            Dict con métricas por workflow (count, total_time, avg_time)
        
        Ejemplo:
            >>> orch = OrchestratorV2()
            >>> # ... procesar varias consultas ...
            >>> metrics = orch.get_metrics()
            >>> print(metrics["simple"]["avg_time"])
        """
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
        """Imprime métricas de rendimiento en formato visual."""
        
        metrics = self.get_metrics()
        
        print("\n" + "="*70)
        print("📊 MÉTRICAS DEL ORCHESTRATOR V2")
        print("="*70)
        
        total_queries = sum(m["total_queries"] for m in metrics.values())
        
        print(f"\n📈 Total de consultas procesadas: {total_queries}")
        print()
        
        for category, data in metrics.items():
            if data["total_queries"] > 0:
                emoji = {
                    "simple": "⚡",
                    "sequential": "🔗",
                    "agentic": "🤖",
                    "conversation": "💬"
                }.get(category, "❓")
                
                print(f"{emoji} {category.upper()}:")
                print(f"   Consultas: {data['total_queries']}")
                print(f"   Tiempo promedio: {data['avg_time']:.2f}s")
                print(f"   Tiempo total: {data['total_time']:.2f}s")
                print()
        
        print("="*70)
    
    def chat(self, thread_id: Optional[str] = None):
        """
        Modo interactivo de chat.
        
        Args:
            thread_id: ID del thread para mantener conversación (opcional)
        
        Comandos especiales:
            - 'salir' o 'exit': Termina el chat y muestra métricas
            - 'nuevo': Crea un nuevo thread (reinicia conversación)
            - 'metrics': Muestra métricas de rendimiento actuales
        
        Ejemplo:
            >>> orch = OrchestratorV2()
            >>> orch.chat()
            👤 Tú: lista campañas
            🤖 Agente: [respuesta]
            👤 Tú: metrics
            [muestra métricas]
            👤 Tú: salir
        """
        
        if not thread_id:
            thread_id = f"interactive_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*70)
        print("💬 MODO CHAT INTERACTIVO V2")
        print(f"   Thread ID: {thread_id}")
        print("   Comandos especiales:")
        print("     - 'salir' o 'exit' para terminar")
        print("     - 'nuevo' para nuevo thread")
        print("     - 'metrics' para ver métricas")
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
                    print(f"\n🔄 Nuevo thread iniciado: {thread_id}\n")
                    continue
                
                if user_input.lower() == 'metrics':
                    self.print_metrics()
                    continue
                
                # Procesar la consulta
                result = self.process_query(user_input, thread_id=thread_id)
                
                # Mostrar respuesta
                print(f"\n🤖 Agente:\n{result.content}\n")
                print("-"*70 + "\n")
            
            except KeyboardInterrupt:
                self.print_metrics()
                print("\n\n👋 Chat interrumpido. ¡Hasta luego!")
                break
            
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


# ========== SCRIPTS DE PRUEBA ==========

def run_day2_demo():
    """Demo rápido del Día 2."""
    
    print("\n" + "🎯"*35)
    print("DEMO DÍA 2: SEQUENTIAL WORKFLOW")
    print("🎯"*35 + "\n")
    
    orchestrator = OrchestratorV2()
    
    queries = [
        # SIMPLE (Fast Path)
        "lista todas las campañas",
        
        # SEQUENTIAL (NUEVO)
        "genera un reporte de Baqueira y envíalo a Slack",
        
        # AGENTIC
        "dame el TOP 3 de anuncios de Baqueira",
        
        # CONVERSATION (con memoria)
        "¿cuál tiene mejor CPA?",
    ]
    
    thread_id = "demo_day2"
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"Query {i}/{len(queries)}: '{query}'")
        print(f"{'='*70}")
        
        result = orchestrator.process_query(query, thread_id=thread_id)
        
        # Mostrar preview de respuesta
        preview = result.content[:300] + "..." if len(result.content) > 300 else result.content
        print(f"\nRespuesta ({result.workflow_type}):\n{preview}\n")
    
    # Mostrar métricas finales
    orchestrator.print_metrics()


def run_simple_test():
    """Test simple para verificar que funciona."""
    
    print("\n🧪 Test Simple de Orchestrator V2\n")
    
    orch = OrchestratorV2()
    
    # Test 1: Consulta simple
    print("TEST 1: Consulta simple")
    result1 = orch.process_query("lista todas las campañas")
    print(f"✓ Workflow: {result1.workflow_type}")
    
    # Test 2: Consulta agéntica
    print("\nTEST 2: Consulta agéntica")
    result2 = orch.process_query("TOP 3 anuncios de Baqueira")
    print(f"✓ Workflow: {result2.workflow_type}")
    
    # Métricas
    orch.print_metrics()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Demo completo del Día 2
        run_day2_demo()
    
    elif len(sys.argv) > 1 and sys.argv[1] == "chat":
        # Modo interactivo
        orchestrator = OrchestratorV2()
        orchestrator.chat()
    
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test simple
        run_simple_test()
    
    else:
        print("\n📝 Uso de orchestrator_v2.py:")
        print("="*50)
        print("  python orchestrator_v2.py demo   - Demo completo")
        print("  python orchestrator_v2.py chat   - Modo interactivo")
        print("  python orchestrator_v2.py test   - Test rápido")
        print("="*50)
        print("\n💡 O importa en tu código:")
        print("  from orchestrator_v2 import OrchestratorV2")
        print("  orch = OrchestratorV2()")
        print("  result = orch.process_query('tu consulta')")
        print()