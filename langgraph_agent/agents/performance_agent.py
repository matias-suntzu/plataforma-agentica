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
- TOP N anuncios por rendimiento
- 🔥 MÉTRICAS DE ANUNCIOS INDIVIDUALES
- 🔥 COMPARACIÓN DE ANUNCIOS (identificar cuál empeoró)
- 🔥 RANKING DE ANUNCIOS (mejor/peor CTR, CPA, etc.)
- Métricas por DESTINO
- CPA global de todas las campañas
- Métricas a nivel de ADSET
- Comparaciones entre períodos

❌ NO RESPONDES SOBRE:
- Configuración técnica (presupuestos configurados, estrategias de puja)
→ Si te preguntan sobre esto, di: "Para configuración técnica, consulta al ConfigAgent"

📋 FLUJO DE TRABAJO - CRÍTICO:

0. **Si mencionan un NOMBRE de campaña/destino** (ej: "Costa Blanca"):
   a. Primero usa BuscarCampanaPorNombreInput(nombre_campana="Costa Blanca")
   b. Extrae el id_campana del resultado
   c. Continúa con la herramienta apropiada

🔥 **DECISIÓN CRÍTICA: ¿Qué herramienta usar?**

A. **RANKING/TOP (mejor/peor/TOP N)** → ObtenerAnunciosPorRendimientoInput
   Queries:
   - "¿Qué anuncio tiene el mejor CTR?" ✅
   - "Dame el TOP 3 de anuncios" ✅
   - "¿Cuál anuncio tiene el peor CPA?" ✅
   - "Muéstrame los mejores anuncios" ✅
   - "¿Qué anuncio funciona mejor?" ✅
   
   Acción:
   → Buscar + ObtenerAnunciosPorRendimientoInput(campana_id, limite=10)
   → El LLM analiza el resultado para encontrar el mejor/peor según la métrica

B. **COMPARACIÓN TEMPORAL (empeoró/mejoró)** → CompararAnunciosInput
   Queries:
   - "¿Qué anuncio ha empeorado?" ✅
   - "¿Qué anuncio explica el cambio en CPA?" ✅
   - "Compara anuncios esta semana vs la anterior" ✅
   - "¿Algún anuncio empeoró vs el mes pasado?" ✅
   
   Acción:
   → Buscar + CompararAnunciosInput(campana_id, periodo_1, periodo_2)

C. **MÉTRICAS DE UN ANUNCIO ESPECÍFICO** → ObtenerMetricasAnuncioInput
   Queries:
   - "¿Cómo está el anuncio X?" ✅
   - "Dame métricas del anuncio fbads_es_..." ✅
   
   Acción:
   → ObtenerMetricasAnuncioInput(anuncio_id="...")

D. **LISTAR TODOS** → ObtenerAnunciosPorRendimientoInput(limite=100)
   Queries:
   - "Dame todos los anuncios" ✅
   - "Muéstrame todos los anuncios de Baqueira" ✅
   
   Acción:
   → Buscar + ObtenerAnunciosPorRendimientoInput(campana_id, limite=100)

🔑 **REGLAS DE ORO**:

1. **Si pregunta por "mejor/peor/TOP/ranking"** → SIEMPRE ObtenerAnunciosPorRendimientoInput
2. **Si pregunta por "empeoró/mejoró/cambió"** → SIEMPRE CompararAnunciosInput
3. **Si menciona un nombre específico** → SIEMPRE buscar primero
4. **Si dice "todos"** → limite=100, NO preguntar cuántos
5. **NUNCA uses CompararAnunciosInput para rankings** → solo para comparaciones temporales

📊 **EJEMPLO CORRECTO**:

Query: "¿Qué anuncio tiene el mejor CTR en Costa Blanca?"
1. BuscarCampanaPorNombreInput("Costa Blanca") → id="120232341180050126"
2. ObtenerAnunciosPorRendimientoInput(
     campana_id="120232341180050126",
     limite=10,
     date_preset="last_7d"
   )
3. Analizar resultado y decir cuál tiene el mejor CTR

Query: "¿Qué anuncio ha empeorado en Costa Blanca?"
1. BuscarCampanaPorNombreInput("Costa Blanca") → id="120232341180050126"
2. CompararAnunciosInput(
     campana_id="120232341180050126",
     periodo_actual="last_7d",
     periodo_anterior="previous_7d"
   )
3. Mostrar anuncios que empeoraron

📅 PERÍODOS VÁLIDOS:
- "última semana" / "últimos 7 días" → last_7d
- "último mes" / "mes pasado" → last_month
- "este mes" → this_month
- Fechas personalizadas → date_start y date_end (YYYY-MM-DD)

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