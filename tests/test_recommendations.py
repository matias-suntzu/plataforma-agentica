# test_recommendations.py

from langgraph_agent.orchestration.orchestrator_v5 import orchestrator_v5

test_queries = [
    # RecommendationAgent
    "dame recomendaciones para mejorar el CPA de Baqueira",
    "¿qué puedo optimizar en todas mis campañas?",
    "¿debería activar Advantage+ en Costa Blanca?",
    
    # Multi-Agent con recommendations
    "analiza la campaña de Baqueira con sugerencias de mejora",
    "reporte completo de Ibiza con recomendaciones",
]

for query in test_queries:
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    result = orchestrator_v5.process_query(query)
    print(f"Workflow: {result.workflow_type}")
    print(f"Respuesta: {result.content[:300]}...")