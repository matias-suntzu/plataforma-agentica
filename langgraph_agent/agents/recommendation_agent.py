"""
Agente de Recomendaciones
Responsabilidad: Analizar configuración y sugerir optimizaciones
"""

import os
from datetime import datetime
from typing import TypedDict, Annotated, List

import json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ..tools.recommendations.recommendation_tools import (
    ObtenerRecomendacionesInput,
    AnalizarOpportunidadInput,
    obtener_recomendaciones_func,
    analizar_oportunidad_func
)

from ..tools.config.config_tools import (
    BuscarCampanaPorNombreInput,
    buscar_campana_por_nombre_func
)

# ========== ESTADO ==========

class RecommendationAgentState(TypedDict):
    """Estado del agente de recomendaciones"""
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]


# ========== HERRAMIENTAS ==========

RECOMMENDATION_TOOLS = [
    ObtenerRecomendacionesInput,
    AnalizarOpportunidadInput,
    BuscarCampanaPorNombreInput,
]


# ========== SYSTEM INSTRUCTION ==========

RECOMMENDATION_AGENT_INSTRUCTION = f"""
Eres un agente especializado en RECOMENDACIONES DE OPTIMIZACIÓN para Meta Ads.

🎯 TU RESPONSABILIDAD:
Responder SOLO preguntas sobre:
- Recomendaciones de mejora (Advantage+, presupuestos, targeting)
- Análisis de oportunidades de optimización
- Sugerencias para reducir CPA/CPC
- Identificar configuraciones subóptimas

❌ NO RESPONDES SOBRE:
- Métricas de rendimiento actuales (gasto, clicks, conversiones) → PerformanceAgent
- Configuración técnica general → ConfigAgent
→ Si te preguntan sobre esto, deriva al agente correcto

📋 FLUJO DE TRABAJO:

1. **Si mencionan un NOMBRE de campaña** (ej: "Baqueira", "Costa Blanca"):
   a. Primero usa BuscarCampanaPorNombreInput(nombre_campana="Baqueira")
   b. Extrae el id_campana del resultado
   c. Luego usa ObtenerRecomendacionesInput(campana_id=ID_OBTENIDO)

2. **Si mencionan un ID directo**:
   → ObtenerRecomendacionesInput(campana_id=X)

3. **Si piden recomendaciones de TODAS**:
   → ObtenerRecomendacionesInput(campana_id="None")

4. **Si piden análisis específico**:
   → AnalizarOpportunidadInput

🔑 REGLAS CRÍTICAS:
- Si mencionan "Baqueira", "Ibiza", "Costa Blanca", etc. → SIEMPRE busca primero con BuscarCampanaPorNombreInput
- NUNCA pidas el ID al usuario si mencionó un nombre de destino/campaña
- Si la búsqueda no encuentra nada, informa al usuario amablemente
- Presenta recomendaciones ordenadas por prioridad: high → medium → low
- Explica el IMPACTO potencial (ej: "9.7% reducción en CPA")
- Incluye ACCIONES concretas ("Activar Advantage+ en adset X")
- NUNCA inventes recomendaciones

📊 PRIORIDADES:
- **HIGH**: Advantage+ no activado (impacto: -9.7% CPA)
- **MEDIUM**: Presupuesto bajo (<10€/día)
- **LOW**: Targeting muy amplio/estrecho

💡 FORMATO DE RESPUESTA:
Para cada recomendación:
1. 🎯 Qué optimizar
2. 📈 Impacto esperado
3. 🔧 Acción concreta
4. ⚡ Prioridad

🗺️ DESTINOS COMUNES:
- **Montaña**: Baqueira, Andorra, Pirineos
- **Islas**: Ibiza, Mallorca, Menorca, Canarias
- **Costas**: Cantabria, Costa de la Luz, Costa Blanca, Costa del Sol

Fecha actual: {datetime.now().strftime('%Y-%m-%d')}
"""


# ========== NODOS ==========

def call_recommendation_llm(state: RecommendationAgentState):
    """Nodo que llama al LLM con herramientas de recomendaciones"""
    messages = state["messages"]
    
    # Agregar system message si no existe
    has_system = any(isinstance(msg, SystemMessage) for msg in messages)
    if not has_system:
        messages = [SystemMessage(content=RECOMMENDATION_AGENT_INSTRUCTION)] + messages
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.0,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    llm_with_tools = llm.bind_tools(RECOMMENDATION_TOOLS)
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}


def execute_recommendation_tools(state: RecommendationAgentState):
    """Ejecuta herramientas de recomendaciones"""
    tool_map = {
        "BuscarCampanaPorNombreInput": (buscar_campana_por_nombre_func, BuscarCampanaPorNombreInput),
        "ObtenerRecomendacionesInput": (obtener_recomendaciones_func, ObtenerRecomendacionesInput),
        "AnalizarOpportunidadInput": (analizar_oportunidad_func, AnalizarOpportunidadInput),
    }
    
    last_message = state["messages"][-1]
    results = []
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {"messages": []}
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.name if hasattr(tool_call, 'name') else tool_call.get('name')
        tool_args = tool_call.args if hasattr(tool_call, 'args') else tool_call.get('args', {})
        tool_id = tool_call.id if hasattr(tool_call, 'id') else tool_call.get('id', 'unknown')
        
        tool_info = tool_map.get(tool_name)
        
        if not tool_info:
            results.append(ToolMessage(
                content=f"Error: Herramienta {tool_name} no encontrada en RecommendationAgent",
                tool_call_id=tool_id
            ))
            continue
        
        tool_func, tool_input_class = tool_info
        
        try:
            tool_input = tool_input_class(**tool_args)
            result = tool_func(tool_input)
            
            # ✅ Manejo específico para BuscarCampanaPorNombreInput
            if tool_name == "BuscarCampanaPorNombreInput":
                content = json.dumps({
                    "id_campana": result.id_campana,
                    "nombre_encontrado": result.nombre_encontrado
                })
            else:
                content = result.datos_json if hasattr(result, 'datos_json') else str(result)
            
            results.append(ToolMessage(content=content, tool_call_id=tool_id))
        
        except Exception as e:
            import traceback
            results.append(ToolMessage(
                content=f"Error ejecutando {tool_name}: {str(e)}\n{traceback.format_exc()}",
                tool_call_id=tool_id
            ))
    
    return {"messages": results}


def should_continue_recommendation(state: RecommendationAgentState) -> str:
    """Decide si continuar o terminar"""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "execute_tools"
    
    return "end"


# ========== CONSTRUCCIÓN DEL GRAFO ==========

def create_recommendation_agent():
    """Crea y compila el agente de recomendaciones"""
    workflow = StateGraph(RecommendationAgentState)
    
    workflow.add_node("call_llm", call_recommendation_llm)
    workflow.add_node("execute_tools", execute_recommendation_tools)
    
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges(
        "call_llm",
        should_continue_recommendation,
        {"execute_tools": "execute_tools", "end": END}
    )
    workflow.add_edge("execute_tools", "call_llm")
    
    # Compilar con memoria
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app


# ========== EXPORTAR ==========

recommendation_agent = create_recommendation_agent()


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing RecommendationAgent...\n")
    
    test_queries = [
        "dame recomendaciones para mejorar el CPA de Baqueira",
        "¿qué puedo optimizar en todas mis campañas?",
        "analiza oportunidades de Advantage+ en Costa Blanca",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        config = {"configurable": {"thread_id": "test_rec_001"}}
        result = recommendation_agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        
        final_message = result["messages"][-1]
        print(f"Respuesta: {final_message.content[:300]}...")