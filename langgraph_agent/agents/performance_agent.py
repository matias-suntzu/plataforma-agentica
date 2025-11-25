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
    comparar_anuncios_globales_func,
    ObtenerFunnelConversionesInput,
    obtener_funnel_conversiones_func,
    ObtenerRankingCampanasInput,
    obtener_ranking_campanas_func,
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

    # 🆕 NUEVO: Ranking de campañas
    ObtenerRankingCampanasInput,
    
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

    # 🆕 Funnel de conversiones
    ObtenerFunnelConversionesInput,
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
- 🆕 FUNNEL DE CONVERSIONES (Subscriber → MQL → SQL → Customer)
- 🆕 RATIOS DE CONVERSIÓN entre etapas del funnel
- 🆕 CPA POR TIPO de conversión
- 🆕 RANKING DE CAMPAÑAS por cualquier métrica
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

🔥 **DECISIÓN CRÍTICA: ¿Qué herramienta usar?**

A. **MÉTRICAS BÁSICAS DE CAMPAÑA** → ObtenerMetricasCampanaInput
   - "¿Cuánto he gastado?" ✅
   - "Conversiones de Baqueira" ✅
   - "Métricas de Costa Blanca" ✅
   - **NUEVO**: Ahora incluye automáticamente métricas del funnel (Subscriber/MQL/SQL/Customer)

B. 🆕 **RANKING DE TODAS LAS CAMPAÑAS** → ObtenerRankingCampanasInput
   Ejemplos:
   - "¿Qué campañas tienen el mejor CPA de registered?" ✅
   - "Dame las campañas con peor CPA de MQL" ✅
   - "TOP 10 campañas por conversiones" ✅
   - "Ranking de campañas por gasto" ✅
   - "Campañas ordenadas por CPA de subscriber" ✅
   - "Lista campañas de mejor a peor por CPA" ✅
   
   **Parámetros clave:**
   - `ordenar_por`: "cpa_subscriber" (o "cpa_registered"), "cpa_mql", "cpa_sql", "cpa_customer", "cpa_total", "spend", "conversiones", "ctr"
   - `orden`: "asc" (mejor primero) o "desc" (peor primero)
   - `limite`: número de campañas (default=10)
   
   **IMPORTANTE**: 
   - "registered" = "subscriber" (son lo mismo)
   - Si piden "mejor CPA" → orden="asc" (menor CPA primero)
   - Si piden "peor CPA" → orden="desc" (mayor CPA primero)

C. **RANKING/TOP N ANUNCIOS** → ObtenerAnunciosPorRendimientoInput
   Ejemplos:
   - "¿Qué anuncio tiene el mejor CTR?" ✅
   - "Dame el TOP 3 de anuncios" ✅
   - "¿Cuál anuncio tiene más clicks?" ✅
   - "TOP 5 anuncios con más MQLs" ✅
   - "¿Qué anuncio genera más SQLs?" ✅

D. **COMPARACIÓN TEMPORAL (empeoró/mejoró)** → CompararAnunciosInput
   - "¿Qué anuncio ha empeorado?" ✅
   - "¿Qué anuncio explica el cambio en CPA?" ✅

E. **MÉTRICAS DE UN ANUNCIO ESPECÍFICO** → ObtenerMetricasAnuncioInput
   - "¿Cómo está el anuncio X?" ✅

F. **LISTAR TODOS LOS ANUNCIOS** → ObtenerAnunciosPorRendimientoInput(limite=100)
   - "Dame todos los anuncios" ✅

G. **ANÁLISIS GLOBAL DE TODAS LAS CAMPAÑAS** → CompararAnunciosGlobalesInput
   - "¿Cómo fueron todas las campañas?" ✅

H. 🆕 **ANÁLISIS DEL FUNNEL DE CONVERSIONES** → ObtenerFunnelConversionesInput
   Ejemplos:
   - "¿Cómo está mi funnel de conversiones?" ✅
   - "Ratio de MQL a SQL de Baqueira" ✅
   - "¿Cuántos subscribers se convirtieron en customers?" ✅

🗺️ DESTINOS DISPONIBLES:
- **Montaña**: Baqueira, Andorra, Pirineos
- **Islas**: Ibiza, Mallorca, Menorca, Canarias
- **Costas**: Cantabria, Costa de la Luz, Costa Blanca, Costa del Sol
- **General**: Campañas sin destino específico

🔑 REGLAS CRÍTICAS:

1. **Si mencionan un NOMBRE** → SIEMPRE busca primero con BuscarCampanaPorNombreInput
2. **NUNCA pidas el ID al usuario** si mencionó un nombre
3. 🆕 **Si preguntan por RANKING/TOP de CAMPAÑAS** → ObtenerRankingCampanasInput
4. 🆕 **Si mencionan "registered"** → es lo mismo que "subscriber"
5. 🆕 **Si piden "mejor/peor CPA"**:
   - "mejor CPA" → orden="asc" (menor primero)
   - "peor CPA" → orden="desc" (mayor primero)
6. 🔥 **Si preguntan "¿qué anuncio empeoró/mejoró?"** → CompararAnunciosInput
7. 🔥 **Si preguntan "¿qué anuncio tiene el mejor/peor X?"** → ObtenerAnunciosPorRendimientoInput(ordenar_por=X)
8. 🔥 **Si dicen "todos" (los anuncios)** → limite=100, NO preguntar cuántos
9. 🔥 **Si dicen "todas" (las campañas)** → CompararAnunciosGlobalesInput, NO preguntar cuál
10. 🆕 **Si mencionan "funnel", "MQL", "SQL", "subscriber", "ratios de conversión"** → ObtenerFunnelConversionesInput
11. Para destinos, usa el nombre exacto (ej: "Costa Blanca", no "costablanca")
12. Presenta métricas con emojis: 💰 (gasto), 👁️ (impresiones), 👆 (clicks), 🎯 (conversiones)
13. 🆕 Usa emojis para el funnel: 📧 (subscriber/registered), 🎯 (MQL), 💼 (SQL), 🛒 (customer)
14. Calcula ratios cuando sea relevante (CTR, ratio conversión, valor/coste)
15. NUNCA inventes métricas

🆕 TIPOS DE CONVERSIÓN DISPONIBLES:
- **Subscriber/Registered** (📧): Suscripciones, leads iniciales, registros
- **MQL** (🎯): Marketing Qualified Lead - Lead calificado por marketing
- **SQL** (💼): Sales Qualified Lead - Lead calificado por ventas
- **Customer** (🛒): Compras, clientes finales

🔥 EJEMPLOS DE CONVERSACIÓN CORRECTA:

Usuario: "de las campañas activas de la semana pasada, lístame en orden cuales han funcionado peor o mejor en función del coste por conversión del registered"
1. ObtenerRankingCampanasInput(
     date_preset="last_7d",
     ordenar_por="cpa_subscriber",  # registered = subscriber
     orden="asc",  # mejor primero (menor CPA)
     limite=10
   )
✅ Respuesta: "Ranking de campañas por CPA de Registered (última semana):
   1. Campaña A: 5.20€
   2. Campaña B: 7.80€
   3. Campaña C: 12.50€
   ..."

Usuario: "¿Qué campañas tienen el peor CPA de MQL?"
1. ObtenerRankingCampanasInput(
     ordenar_por="cpa_mql",
     orden="desc",  # peor primero (mayor CPA)
     limite=5
   )

Usuario: "TOP 10 campañas por conversiones totales"
1. ObtenerRankingCampanasInput(
     ordenar_por="conversiones",
     orden="desc",  # más conversiones primero
     limite=10
   )

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
        model="gemini-2.5-flash",
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
        
        # 🆕 NUEVO: Ranking de campañas
        "ObtenerRankingCampanasInput": (obtener_ranking_campanas_func, ObtenerRankingCampanasInput),
        
        # 🔥 Anuncios
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
        
        # Funnel de conversiones
        "ObtenerFunnelConversionesInput": (obtener_funnel_conversiones_func, ObtenerFunnelConversionesInput),
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
    print("\n🧪 Testing PerformanceAgent con Funnel de Conversiones...\n")
    
    test_queries = [
        "¿cuánto he gastado en Baqueira esta semana?",
        "¿cómo está mi funnel de conversiones?",
        "ratio de MQL a SQL de Baqueira",
        "TOP 3 anuncios con más MQLs",
        "¿qué anuncio genera más SQLs?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        config = {"configurable": {"thread_id": "test_perf_funnel_001"}}
        result = performance_agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        
        final_message = result["messages"][-1]
        print(f"Respuesta: {final_message.content[:300]}...")