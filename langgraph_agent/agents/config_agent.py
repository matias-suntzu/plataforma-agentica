"""
Agente de Configuración
Responsabilidad: Responder preguntas sobre configuración técnica de campañas
"""

import os
from datetime import datetime
from typing import TypedDict, Annotated, List

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ..tools.config.config_tools import (
    ListarCampanasInput,
    BuscarCampanaPorNombreInput,
    ObtenerDetallesCampanaInput,
    ObtenerPresupuestoInput,
    ObtenerEstrategiaPujaInput,
    listar_campanas_func,
    buscar_campana_por_nombre_func,
    obtener_detalles_campana_func,
    obtener_presupuesto_func,
    obtener_estrategia_puja_func
)


# ========== ESTADO ==========

class ConfigAgentState(TypedDict):
    """Estado del agente de configuración"""
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]


# ========== HERRAMIENTAS ==========

CONFIG_TOOLS = [
    ListarCampanasInput,
    BuscarCampanaPorNombreInput,
    ObtenerDetallesCampanaInput,
    ObtenerPresupuestoInput,
    ObtenerEstrategiaPujaInput,
]


# ========== SYSTEM INSTRUCTION ==========

CONFIG_AGENT_INSTRUCTION = f"""
Eres un agente especializado en CONFIGURACIÓN TÉCNICA de campañas de Meta Ads.

🎯 TU RESPONSABILIDAD:
Responder SOLO preguntas sobre:
- Listados de campañas
- Búsqueda de campañas por nombre
- Presupuestos (diario, lifetime, restante)
- Estrategias de puja
- Objetivos de campaña
- Configuración de adsets (targeting, Advantage+)
- Estado de campañas (activa, pausada)

❌ NO RESPONDES SOBRE:
- Métricas de rendimiento (gasto, clicks, conversiones, CTR, CPM)
- Comparaciones de períodos
- Análisis de resultados
- Recomendaciones de optimización
→ Si te preguntan sobre esto, deriva al agente correcto:
  - Métricas → PerformanceAgent
  - Recomendaciones → RecommendationAgent

📋 FLUJO DE TRABAJO:

1. **Si mencionan un nombre de campaña** → Usa BuscarCampanaPorNombreInput
   - Ejemplo: "presupuesto de Baqueira"
   - Primero busca por nombre, luego usa el ID

2. **Si piden presupuesto** → Usa ObtenerPresupuestoInput
   - Más rápido que obtener_detalles_campana_func
   - Solo retorna presupuestos

3. **Si piden estrategia** → Usa ObtenerEstrategiaPujaInput
   - Más rápido que obtener_detalles_campana_func
   - Solo retorna estrategia de puja

4. **Si piden "todo sobre la campaña"** → Usa ObtenerDetallesCampanaInput
   - Incluye: presupuestos, estrategia, adsets, targeting
   - Más completo pero más lento

5. **Si piden listar** → Usa ListarCampanasInput
   - Listado simple de campañas
   - Filtra por estado (ACTIVE, PAUSED, ARCHIVED)

🔑 REGLAS CRÍTICAS:
- NUNCA inventes información
- Siempre usa las herramientas disponibles
- Si no encuentras una campaña por nombre, ofrece listar todas
- Responde en español de forma clara y concisa
- Si no tienes la herramienta para algo, dilo claramente

📊 FORMATO DE RESPUESTAS:
- Usa emojis para claridad: 💰 (presupuesto), 🎯 (objetivo), ⚙️ (estrategia)
- Presenta números en formato legible (ej: 1,234.56€)
- Indica claramente el estado de cada campaña/adset

🗺️ DESTINOS DISPONIBLES:
El sistema reconoce automáticamente estos destinos en nombres:
- **Montaña**: Baqueira, Andorra, Pirineos
- **Islas**: Ibiza, Mallorca, Menorca, Canarias
- **Costas**: Cantabria, Costa de la Luz, Costa Blanca, Costa del Sol

Fecha actual: {datetime.now().strftime('%Y-%m-%d')}
"""


# ========== NODOS ==========

def call_config_llm(state: ConfigAgentState):
    """Nodo que llama al LLM con herramientas de configuración"""
    messages = state["messages"]
    
    # Agregar system message si no existe
    has_system = any(isinstance(msg, SystemMessage) for msg in messages)
    if not has_system:
        messages = [SystemMessage(content=CONFIG_AGENT_INSTRUCTION)] + messages
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.0,
        google_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )
    
    llm_with_tools = llm.bind_tools(CONFIG_TOOLS)
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}


def execute_config_tools(state: ConfigAgentState):
    """Ejecuta herramientas de configuración"""
    tool_map = {
        "ListarCampanasInput": (listar_campanas_func, ListarCampanasInput),
        "BuscarCampanaPorNombreInput": (buscar_campana_por_nombre_func, BuscarCampanaPorNombreInput),
        "ObtenerDetallesCampanaInput": (obtener_detalles_campana_func, ObtenerDetallesCampanaInput),
        "ObtenerPresupuestoInput": (obtener_presupuesto_func, ObtenerPresupuestoInput),
        "ObtenerEstrategiaPujaInput": (obtener_estrategia_puja_func, ObtenerEstrategiaPujaInput),
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
                content=f"Error: Herramienta {tool_name} no encontrada en ConfigAgent",
                tool_call_id=tool_id
            ))
            continue
        
        tool_func, tool_input_class = tool_info
        
        try:
            tool_input = tool_input_class(**tool_args)
            result = tool_func(tool_input)
            
            # Extraer contenido según tipo de output
            if hasattr(result, 'campanas_json'):
                content = result.campanas_json
            elif hasattr(result, 'datos_json'):
                content = result.datos_json
            elif hasattr(result, 'id_campana'):
                import json
                content = json.dumps({
                    "id_campana": result.id_campana,
                    "nombre_encontrado": result.nombre_encontrado
                })
            else:
                content = str(result)
            
            results.append(ToolMessage(content=content, tool_call_id=tool_id))
        
        except Exception as e:
            import traceback
            results.append(ToolMessage(
                content=f"Error ejecutando {tool_name}: {str(e)}\n{traceback.format_exc()}",
                tool_call_id=tool_id
            ))
    
    return {"messages": results}


def should_continue_config(state: ConfigAgentState) -> str:
    """Decide si continuar o terminar"""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "execute_tools"
    
    return "end"


# ========== CONSTRUCCIÓN DEL GRAFO ==========

def create_config_agent():
    """Crea y compila el agente de configuración"""
    workflow = StateGraph(ConfigAgentState)
    
    workflow.add_node("call_llm", call_config_llm)
    workflow.add_node("execute_tools", execute_config_tools)
    
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges(
        "call_llm",
        should_continue_config,
        {"execute_tools": "execute_tools", "end": END}
    )
    workflow.add_edge("execute_tools", "call_llm")
    
    # Compilar con memoria
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app


# ========== EXPORTAR ==========

config_agent = create_config_agent()


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing ConfigAgent...\n")
    
    test_queries = [
        "lista todas las campañas activas",
        "¿qué presupuesto tiene la campaña de Baqueira?",
        "estrategia de puja de Ibiza",
        "dame todos los detalles de Costa Blanca",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        config = {"configurable": {"thread_id": "test_config_001"}}
        result = config_agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        
        final_message = result["messages"][-1]
        print(f"Respuesta: {final_message.content[:200]}...")