"""
Agente de Rendimiento
Responsabilidad: Responder preguntas sobre métricas, gasto, conversiones y comparaciones
"""

import os
from datetime import datetime
from typing import TypedDict, Annotated, List

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from ..tools.performance.performance_tools import (
    ObtenerMetricasCampanaInput,
    ObtenerAnunciosPorRendimientoInput,
    CompararPeriodosInput,
    ObtenerMetricasGlobalesInput,
    obtener_metricas_campana_func,
    obtener_anuncios_por_rendimiento_func,
    comparar_periodos_func,
    obtener_metricas_globales_func,
    ObtenerMetricasPorDestinoInput,
    ObtenerCPAGlobalInput,
    ObtenerMetricasAdsetInput,
    CompararDestinosInput,
    obtener_metricas_por_destino_func,
    obtener_cpa_global_func,
    obtener_metricas_adset_func,
    comparar_destinos_func,
)


# ========== ESTADO ==========

class PerformanceAgentState(TypedDict):
    """Estado del agente de rendimiento"""
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]


# ========== HERRAMIENTAS ==========

PERFORMANCE_TOOLS = [
    # Existentes
    ObtenerMetricasCampanaInput,
    ObtenerAnunciosPorRendimientoInput,
    CompararPeriodosInput,
    ObtenerMetricasGlobalesInput,
    
    # 🆕 Nuevas
    ObtenerMetricasPorDestinoInput,
    ObtenerCPAGlobalInput,
    ObtenerMetricasAdsetInput,
    CompararDestinosInput,
]


# ========== SYSTEM INSTRUCTION ==========

PERFORMANCE_AGENT_INSTRUCTION = f"""
Eres un agente especializado en MÉTRICAS DE RENDIMIENTO de campañas de Meta Ads.

🎯 TU RESPONSABILIDAD:
Responder SOLO preguntas sobre:
- Gasto (cuánto se ha gastado)
- Impresiones, clicks, CTR
- CPM, CPC, CPA
- Conversiones (totales y por tipo)
- Ratio de conversiones
- Valor de conversión vs coste
- TOP N anuncios por rendimiento
- 🆕 Métricas por DESTINO (Baqueira, Ibiza, Costa Blanca, etc.)
- 🆕 CPA global de todas las campañas
- 🆕 Métricas a nivel de ADSET
- 🆕 Comparaciones entre períodos
- 🆕 Comparaciones entre destinos

❌ NO RESPONDES SOBRE:
- Configuración técnica (presupuestos configurados, estrategias de puja, targeting)
- Listados de campañas sin métricas
→ Si te preguntan sobre esto, di: "Para configuración técnica, consulta al ConfigAgent"

📋 FLUJO DE TRABAJO:

1. **Métricas de UNA campaña**:
   - "gasto de Baqueira" → ObtenerMetricasCampanaInput

2. **TOP anuncios**:
   - "TOP 3 anuncios de Costa Blanca" → ObtenerAnunciosPorRendimientoInput

3. **Comparar períodos**:
   - "compara esta semana con la anterior" → CompararPeriodosInput
   - "Baqueira la semana pasada vs resto del mes" → CompararPeriodosInput

4. **Métricas globales**:
   - "CPA global de las campañas" → ObtenerCPAGlobalInput
   - "métricas de todas las campañas" → ObtenerMetricasGlobalesInput

5. 🆕 **Métricas por DESTINO**:
   - "¿qué destinos funcionaron mejor?" → ObtenerMetricasPorDestinoInput
   - "¿cuánto se gastó en Costa Blanca en septiembre?" → ObtenerMetricasPorDestinoInput(destino="Costa Blanca", date_start="2025-09-01", date_end="2025-09-30")

6. 🆕 **Métricas de ADSETS**:
   - "dame los adsets de Baqueira" → ObtenerMetricasAdsetInput

7. 🆕 **Comparar DESTINOS**:
   - "compara Baqueira vs Ibiza" → CompararDestinosInput(destinos=["Baqueira", "Ibiza"])

🗺️ DESTINOS DISPONIBLES:
- **Montaña**: Baqueira, Andorra, Pirineos
- **Islas**: Ibiza, Mallorca, Menorca, Canarias
- **Costas**: Cantabria, Costa de la Luz, Costa Blanca, Costa del Sol
- **General**: Campañas sin destino específico

🔑 REGLAS CRÍTICAS:
- SIEMPRE pregunta por el ID de campaña si no lo mencionan (o usa búsqueda)
- Para destinos, usa el nombre exacto (ej: "Costa Blanca", no "costablanca")
- Para periodos, detecta los 2 períodos mencionados
- Presenta métricas con emojis: 💰 (gasto), 👁️ (impresiones), 👆 (clicks), 🎯 (conversiones)
- Calcula ratios cuando sea relevante (CTR, ratio conversión, valor/coste)
- NUNCA inventes métricas

📅 PERÍODOS VÁLIDOS DE META ADS API:

**IMPORTANTE**: Traduce SIEMPRE las expresiones humanas a estos presets válidos:

| Usuario dice | Usa en API |
|--------------|------------|
| "última semana" / "semana pasada" | `last_7d` |
| "últimos 7 días" | `last_7d` |
| "últimos 14 días" | `last_14d` |
| "últimos 28 días" / "último mes" | `last_28d` |
| "este mes" / "mes actual" | `this_month` |
| "mes pasado" | `last_month` |
| "hoy" | `today` |
| "ayer" | `yesterday` |
| Fechas específicas | Usa `date_start` y `date_end` en formato YYYY-MM-DD |

⚠️ **NO USES ESTOS** (no existen en Meta API):
- ❌ `last_week`
- ❌ `this_week`
- ❌ `previous_7d`

🆕 COMPARACIONES:
Cuando el usuario pida "esta semana vs la anterior":
- Periodo 1: Usa fechas custom (lunes de esta semana hasta hoy)
- Periodo 2: Usa fechas custom (lunes-domingo de semana pasada)

**Ejemplo de conversión**:
Usuario: "¿qué destinos funcionaron mejor la semana pasada?"
→ Usa: `date_preset="last_7d"` (NO uses "last_week")

Usuario: "compara esta semana con la anterior"
→ Usa: `periodo_1="custom"` con fechas calculadas
→ Usa: `periodo_2="custom"` con fechas de semana anterior

Fecha actual: {datetime.now().strftime('%Y-%m-%d')}
"""


# ========== NODOS ==========

def call_performance_llm(state: PerformanceAgentState):
    """Nodo que llama al LLM con herramientas de rendimiento"""
    messages = state["messages"]
    
    # Agregar system message si no existe
    has_system = any(isinstance(msg, SystemMessage) for msg in messages)
    if not has_system:
        messages = [SystemMessage(content=PERFORMANCE_AGENT_INSTRUCTION)] + messages
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.0,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    llm_with_tools = llm.bind_tools(PERFORMANCE_TOOLS)
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}


def execute_performance_tools(state: PerformanceAgentState):
    """Ejecuta herramientas de rendimiento"""
    tool_map = {
    # Existentes
    "ObtenerMetricasCampanaInput": (obtener_metricas_campana_func, ObtenerMetricasCampanaInput),
    "ObtenerAnunciosPorRendimientoInput": (obtener_anuncios_por_rendimiento_func, ObtenerAnunciosPorRendimientoInput),
    "CompararPeriodosInput": (comparar_periodos_func, CompararPeriodosInput),
    "ObtenerMetricasGlobalesInput": (obtener_metricas_globales_func, ObtenerMetricasGlobalesInput),
    
    # 🆕 Nuevas
    "ObtenerMetricasPorDestinoInput": (obtener_metricas_por_destino_func, ObtenerMetricasPorDestinoInput),
    "ObtenerCPAGlobalInput": (obtener_cpa_global_func, ObtenerCPAGlobalInput),
    "ObtenerMetricasAdsetInput": (obtener_metricas_adset_func, ObtenerMetricasAdsetInput),
    "CompararDestinosInput": (comparar_destinos_func, CompararDestinosInput),
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
                content=f"Error: Herramienta {tool_name} no encontrada en PerformanceAgent",
                tool_call_id=tool_id
            ))
            continue
        
        tool_func, tool_input_class = tool_info
        
        try:
            tool_input = tool_input_class(**tool_args)
            result = tool_func(tool_input)
            
            # Extraer contenido
            content = result.datos_json if hasattr(result, 'datos_json') else str(result)
            
            results.append(ToolMessage(content=content, tool_call_id=tool_id))
        
        except Exception as e:
            import traceback
            results.append(ToolMessage(
                content=f"Error ejecutando {tool_name}: {str(e)}\n{traceback.format_exc()}",
                tool_call_id=tool_id
            ))
    
    return {"messages": results}


def should_continue_performance(state: PerformanceAgentState) -> str:
    """Decide si continuar o terminar"""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "execute_tools"
    
    return "end"


# ========== CONSTRUCCIÓN DEL GRAFO ==========

def create_performance_agent():
    """Crea y compila el agente de rendimiento"""
    workflow = StateGraph(PerformanceAgentState)
    
    workflow.add_node("call_llm", call_performance_llm)
    workflow.add_node("execute_tools", execute_performance_tools)
    
    workflow.set_entry_point("call_llm")
    workflow.add_conditional_edges(
        "call_llm",
        should_continue_performance,
        {"execute_tools": "execute_tools", "end": END}
    )
    workflow.add_edge("execute_tools", "call_llm")
    
    # Compilar con memoria
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app


# ========== EXPORTAR ==========

performance_agent = create_performance_agent()


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing PerformanceAgent...\n")
    
    test_queries = [
        "¿cuánto he gastado en Baqueira esta semana?",
        "dame el TOP 3 de anuncios de Ibiza",
        "compara esta semana con la anterior",
        "métricas globales de todas las campañas",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        config = {"configurable": {"thread_id": "test_perf_001"}}
        result = performance_agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        
        final_message = result["messages"][-1]
        print(f"Respuesta: {final_message.content[:200]}...")