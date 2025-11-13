"""
Sequential Workflow - VERSIÓN UNIFICADA
"""
from .base import WorkflowResult, AgenticWorkflow

class SequentialWorkflow:
    """Workflow SEQUENTIAL - Flujos multi-paso predefinidos."""
    
    def __init__(self, agent_app):
        """
        ✅ CAMBIO: Ya NO recibe langserve_url ni api_key
        
        Args:
            agent_app: Instancia del agente LangGraph compilado
        """
        self.agent_app = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """Ejecuta el flujo secuencial."""
        print(f"\n🔗 SEQUENTIAL WORKFLOW")
        print(f"   Query: '{query}'")
        
        # Delegar al workflow agéntico
        agentic = AgenticWorkflow(self.agent_app)
        result = agentic.execute(query, thread_id)
        result.workflow_type = "sequential"
        
        return result