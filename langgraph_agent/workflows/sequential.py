"""
Sequential Workflow
"""
from .base import WorkflowResult, AgenticWorkflow

class SequentialWorkflow:
    """Workflow SEQUENTIAL - Flujos multi-paso predefinidos."""
    
    def __init__(self, langserve_url: str, api_key: str, agent_app):
        self.langserve_url = langserve_url
        self.api_key = api_key
        self.agent_app = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """Ejecuta el flujo secuencial."""
        print(f"\n🔗 SEQUENTIAL WORKFLOW")
        print(f"   Query: '{query}'")
        
        agentic = AgenticWorkflow(self.agent_app)
        result = agentic.execute(query, thread_id)
        result.workflow_type = "sequential"
        
        return result