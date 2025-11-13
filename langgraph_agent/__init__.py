"""
LangGraph Agent Package
NO importar NADA aquí para evitar ciclos circulares
"""

# ❌ NO HACER ESTO (causa imports circulares):
# from .orchestration.orchestrator import OrchestratorV3
# from .core.agent import app

# ✅ Dejar vacío o solo metadata
__version__ = "3.3.0"
__author__ = "Meta Ads Agent Team"

# Los imports se harán directamente donde se necesiten:
# from langgraph_agent.orchestration import OrchestratorV3
# from langgraph_agent.core.agent import app