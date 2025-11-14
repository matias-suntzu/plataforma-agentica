"""
Conversation Workflow
"""
from .base import WorkflowResult, AgenticWorkflow
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

class ConversationWorkflow:
    """
    Workflow conversacional.
    ✅ USA RunnableConfig con thread_id
    """
    
    def __init__(self, agent_app):
        self.agent_app = agent_app
        print("💬 ConversationWorkflow inicializado (con memoria)")
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """
        Ejecuta workflow conversacional CON memoria.
        """
        print(f"💬 CONVERSATION WORKFLOW")
        print(f"   Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        
        try:
            # ✅ IMPORTANTE: Configurar con thread_id
            config = RunnableConfig(
                configurable={"thread_id": thread_id}
            )
            
            input_message = HumanMessage(content=query)
            
            # ✅ Invocar con config
            result = self.agent_app.invoke(
                {"messages": [input_message]},
                config=config
            )
            
            # Extraer respuesta
            final_message = result["messages"][-1]
            content = final_message.content if isinstance(final_message.content, str) else str(final_message.content)
            
            return WorkflowResult(
                content=content,
                workflow_type="conversation",
                metadata={"thread_id": thread_id}
            )
        
        except Exception as e:
            print(f"   ❌ Error en conversation workflow: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return WorkflowResult(
                content=f"❌ Error: {str(e)}",
                workflow_type="conversation",
                metadata={"error": str(e), "thread_id": thread_id}
            )