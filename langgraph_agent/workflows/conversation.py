"""
Conversation Workflow
"""
from .base import WorkflowResult, AgenticWorkflow

class ConversationWorkflow:
    """Workflow CONVERSACIONAL - Preguntas de seguimiento."""
    
    def __init__(self, agent_app):
        self.agent = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """Ejecuta pregunta de seguimiento."""
        print(f"\n💬 CONVERSATION WORKFLOW")
        print(f"   Query: '{query}'")
        print(f"   🧠 Usando memoria conversacional...")
        
        agentic = AgenticWorkflow(self.agent)
        result = agentic.execute(query, thread_id)
        result.workflow_type = "conversation"
        
        return result