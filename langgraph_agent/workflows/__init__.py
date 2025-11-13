"""
Workflows del agente
"""

from .base import (
    WorkflowResult,
    FastPathWorkflow,
    AgenticWorkflow
)
from .sequential import SequentialWorkflow
from .conversation import ConversationWorkflow
from .autonomous import AutonomousOptimizationWorkflow

__all__ = [
    'WorkflowResult',
    'FastPathWorkflow',
    'AgenticWorkflow',
    'SequentialWorkflow',
    'ConversationWorkflow',
    'AutonomousOptimizationWorkflow'
]