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

import json

from ..tools.config.config_tools import (
    BuscarCampanaPorNombreInput,
    buscar_campana_por_nombre_func
)

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
    ObtenerMetricasAnuncioInput,
    CompararAnunciosInput,
    obtener_metricas_anuncio_func,
    comparar_anuncios_func,
    CompararAnunciosGlobalesInput,
    comparar_anuncios_globales_func
)


# ========== ESTADO ==========

class PerformanceAgentState(TypedDict):
    """Estado del agente de rendimiento"""
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]


# ========== HERRAMIENTAS ==========

PERFORMANCE_TOOLS = [
    # Búsqueda
    BuscarCampanaPorNombreInput,

    # Métricas de campaña y globales
    ObtenerMetricasCampanaInput,
    ObtenerMetricasGlobalesInput,
    
    # 🔥 Anuncios
    ObtenerAnunciosPorRendimientoInput,
    ObtenerMetricasAnuncioInput,
    CompararAnunciosInput,
    CompararAnunciosGlobalesInput,
    
    # Comparaciones
    CompararPeriodosInput,
    
    # Por destino
    ObtenerMetricasPorDestinoInput,
    CompararDestinosInput,
    
    # Otras
    ObtenerCPAGlobalInput,
    ObtenerMetricasAdsetInput,
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
- 🔥 MÉTRICAS DE ANUNCIOS INDIVIDUALES
- 🔥 COMPARACIÓN DE ANUNCIOS (identificar cuál empeoró)
- 🔥 ANÁLISIS DE ANUNCIOS QUE EXPLICAN CAMBIOS EN MÉTRICAS
- 🔥 RANKING/TOP N ANUNCIOS POR CUALQUIER MÉTRICA
- Métricas por DESTINO (Baqueira, Ibiza, Costa Blanca, etc.)
- CPA global de todas las campañas
- Métricas a nivel de ADSET
- Comparaciones entre períodos
- Comparaciones entre destinos

❌ NO RESPONDES SOBRE:
- Configuración técnica (presupuestos configurados, estrategias de puja, targeting)
- Listados de campañas sin métricas
→ Si te preguntan sobre esto, di: "Para configuración técnica, consulta al ConfigAgent"

📋 FLUJO DE TRABAJO:

0. **Si mencionan un NOMBRE de campaña/destino** (ej: "Baqueira", "Costa Blanca"):
   a. Primero usa BuscarCampanaPorNombreInput(nombre_campana="Baqueira")
   b. Extrae el id_campana del resultado
   c. Continúa con la herramienta apropiada usando ese ID

🔥 **DECISIÓN CRÍTICA: ¿Qué herramienta usar para ANUNCIOS?**

A. **RANKING/TOP N (mejor/peor/TOP por métrica)** → ObtenerAnunciosPorRendimientoInput
   Ejemplos:
   - "¿Qué anuncio tiene el mejor CTR?" ✅
   - "Dame el TOP 3 de anuncios" ✅
   - "¿Cuál anuncio tiene más clicks?" ✅
   - "TOP 5 anuncios con mejor CPA" ✅
   - "¿Qué anuncio tiene el peor CPA?" ✅
   
   **Parámetros clave:**
   - `ordenar_por`: "clicks" (default), "ctr", "cpa", "conversiones", "impressions", "cpc", "spend"
   - `limite`: número de anuncios (default=3)
   
   **IMPORTANTE**: Si preguntan por "mejor/peor X", usar esta herramienta con `ordenar_por=X`

B. **COMPARACIÓN TEMPORAL (empeoró/mejoró entre períodos)** → CompararAnunciosInput
   Ejemplos:
   - "¿Qué anuncio ha empeorado?" ✅
   - "¿Qué anuncio explica el cambio en CPA?" ✅
   - "¿Qué anuncios empeoraron vs la semana pasada?" ✅
   - "¿Hay algún anuncio que explique el aumento del CPA?" ✅
   
   **IMPORTANTE**: Si preguntan por "empeoró/mejoró/cambió", usar ESTA herramienta

C. **MÉTRICAS DE UN ANUNCIO ESPECÍFICO** → ObtenerMetricasAnuncioInput
   Ejemplos:
   - "¿Cómo está el anuncio X?" ✅
   - "Dame métricas del anuncio fbads_es_..." ✅
   
D. **LISTAR TODOS LOS ANUNCIOS** → ObtenerAnunciosPorRendimientoInput(limite=100)
   Ejemplos:
   - "Dame todos los anuncios" ✅
   - "Muéstrame todos los anuncios de Baqueira" ✅
   
   **IMPORTANTE**: Si dicen "todos", NO preguntes cuántos, usa limite=100 automáticamente

E. **ANÁLISIS GLOBAL DE TODAS LAS CAMPAÑAS** → CompararAnunciosGlobalesInput
   Ejemplos:
   - "¿Cómo fueron todas las campañas?" ✅
   - "Analiza todos los anuncios de todas las campañas" ✅
   - "¿Qué anuncios empeoraron en general?" ✅
   
   **IMPORTANTE**: Si dicen "todas (las campañas)", NO preguntes "¿de qué campaña?"

🗺️ DESTINOS DISPONIBLES:
- **Montaña**: Baqueira, Andorra, Pirineos
- **Islas**: Ibiza, Mallorca, Menorca, Canarias
- **Costas**: Cantabria, Costa de la Luz, Costa Blanca, Costa del Sol
- **General**: Campañas sin destino específico

🔑 REGLAS CRÍTICAS:

1. **Si mencionan un NOMBRE** → SIEMPRE busca primero con BuscarCampanaPorNombreInput
2. **NUNCA pidas el ID al usuario** si mencionó un nombre
3. **Si la búsqueda retorna id_campana="None"**, informa que no se encontró esa campaña
4. 🔥 **Si preguntan "¿qué anuncio empeoró/mejoró?"** → CompararAnunciosInput
5. 🔥 **Si preguntan "¿qué anuncio tiene el mejor/peor X?"** → ObtenerAnunciosPorRendimientoInput(ordenar_por=X)
6. 🔥 **Si dicen "todos" (los anuncios)** → limite=100, NO preguntar cuántos
7. 🔥 **Si dicen "todas" (las campañas)** → CompararAnunciosGlobalesInput, NO preguntar cuál
8. Para destinos, usa el nombre exacto (ej: "Costa Blanca", no "costablanca")
9. Presenta métricas con emojis: 💰 (gasto), 👁️ (impresiones), 👆 (clicks), 🎯 (conversiones)
10. Calcula ratios cuando sea relevante (CTR, ratio conversión, valor/coste)
11. NUNCA inventes métricas

📅 PERÍODOS VÁLIDOS:
- "última semana" / "últimos 7 días" → last_7d
- "último mes" / "mes pasado" → last_month
- "este mes" → this_month
- "esta semana" → this_week
- "semana pasada" → last_week
- Fechas personalizadas → date_start y date_end (YYYY-MM-DD)

🔥 EJEMPLOS DE CONVERSACIÓN CORRECTA:

Usuario: "¿Qué anuncio tiene el mejor CTR en Costa Blanca?"
1. BuscarCampanaPorNombreInput(nombre_campana="Costa Blanca")
2. ObtenerAnunciosPorRendimientoInput(campana_id="...", ordenar_por="ctr", limite=1)
✅ Respuesta: "El anuncio X tiene el mejor CTR con Y%"

Usuario: "¿Hay algún anuncio que ha empeorado y que explique el cambio en el CPA?"
1. Buscar campaña en contexto
2. CompararAnunciosInput(campana_id="...", periodo_actual="last_7d", periodo_anterior="previous_7d")
✅ Respuesta: "Sí, el anuncio X empeoró un Z% en CPA"

Usuario: "Dame todos los anuncios"
1. Buscar campaña en contexto
2. ObtenerAnunciosPorRendimientoInput(campana_id="...", limite=100)
✅ Respuesta: Lista completa de anuncios (NO preguntar "¿cuántos?")

Usuario: "¿Cómo fueron todas las campañas?"
1. CompararAnunciosGlobalesInput(periodo_actual="last_7d", periodo_anterior="previous_7d")
✅ Respuesta: Análisis de todas las campañas (NO preguntar "¿de qué campaña?")

Fecha actual: {datetime.now().strftime('%Y-%m-%d')}
"""

# ========== NODOS ==========

def call_performance_llm(state: PerformanceAgentState):
    """Nodo que llama al LLM con herramientas de rendimiento"""
    messages = state["messages"]
    
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
        # Búsqueda
        "BuscarCampanaPorNombreInput": (buscar_campana_por_nombre_func, BuscarCampanaPorNombreInput),
        
        # Métricas de campaña
        "ObtenerMetricasCampanaInput": (obtener_metricas_campana_func, ObtenerMetricasCampanaInput),
        "ObtenerMetricasGlobalesInput": (obtener_metricas_globales_func, ObtenerMetricasGlobalesInput),
        
        # 🔥 Anuncios (CORREGIDO)
        "ObtenerAnunciosPorRendimientoInput": (obtener_anuncios_por_rendimiento_func, ObtenerAnunciosPorRendimientoInput),
        "ObtenerMetricasAnuncioInput": (obtener_metricas_anuncio_func, ObtenerMetricasAnuncioInput),
        "CompararAnunciosInput": (comparar_anuncios_func, CompararAnunciosInput),
        "CompararAnunciosGlobalesInput": (comparar_anuncios_globales_func, CompararAnunciosGlobalesInput),
        
        # Comparaciones
        "CompararPeriodosInput": (comparar_periodos_func, CompararPeriodosInput),
        
        # Por destino
        "ObtenerMetricasPorDestinoInput": (obtener_metricas_por_destino_func, ObtenerMetricasPorDestinoInput),
        "CompararDestinosInput": (comparar_destinos_func, CompararDestinosInput),
        
        # Otras
        "ObtenerCPAGlobalInput": (obtener_cpa_global_func, ObtenerCPAGlobalInput),
        "ObtenerMetricasAdsetInput": (obtener_metricas_adset_func, ObtenerMetricasAdsetInput),
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
    
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app


# ========== EXPORTAR ==========

performance_agent = create_performance_agent()


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing PerformanceAgent...\n")
    
    test_queries = [
        "¿Qué anuncio tiene el mejor CTR en Costa Blanca?",
        "¿Hay algún anuncio que ha empeorado?",
        "Dame todos los anuncios de Baqueira",
        "¿Cómo fueron todas las campañas vs la semana pasada?",
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