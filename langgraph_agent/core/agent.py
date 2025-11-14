"""
Agente Principal de Meta Ads con LangGraph
Versión: 3.4 (Con MemorySaver + LangSmith)
"""

import os
import json
import uuid
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver  # ✅ CRITICAL: Para memoria
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

# ========== CONFIGURACIÓN ==========
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "meta-ads-agent"

GEMINI_MODEL = "gemini-2.0-flash-exp"

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("Falta GEMINI_API_KEY")

# Verificar LangSmith (opcional, solo para logs)
if os.getenv("LANGSMITH_API_KEY"):
    print("✅ LangSmith configurado")
else:
    print("⚠️ LangSmith no configurado (continúa sin tracing)")

# ========== ESTADO DEL AGENTE ==========
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]

# ========== ESQUEMAS DE HERRAMIENTAS ==========
class ObtenerAnunciosPorRendimientoInput(BaseModel):
    campana_id: str = Field(description="ID de la campaña")
    date_preset: Optional[str] = Field(default=None, description="'last_7d', 'last_month', etc.")
    date_start: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    date_end: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    limite: int = Field(default=3, description="TOP N anuncios")

class BuscarIdCampanaInput(BaseModel):
    nombre_campana: str = Field(description="Nombre o parte del nombre de campaña")

class EnviarAlertaSlackInput(BaseModel):
    mensaje: str = Field(description="Mensaje a Slack")

class ListarCampanasInput(BaseModel):
    limite: int = Field(default=20, description="Límite de campañas")

class GenerarReporteGoogleSlidesInput(BaseModel):
    resumen_ejecutivo: str = Field(description="Resumen ejecutivo")
    datos_tabla_json: str = Field(description="Datos JSON de anuncios")

class GetAllCampaignsMetricsInput(BaseModel):
    date_preset: str = Field(default="last_30d")
    metrics: List[str] = Field(default=["spend", "clicks", "ctr", "cpm", "cpc"])

class GetCampaignRecommendationsInput(BaseModel):
    campana_id: Optional[str] = Field(default=None, description="ID campaña (None = todas)")

class GetCampaignDetailsInput(BaseModel):
    campana_id: str = Field(description="ID de la campaña")
    include_adsets: bool = Field(default=True, description="Incluir detalles de adsets")

class UpdateAdsetBudgetInput(BaseModel):
    adset_id: str = Field(description="ID del adset a actualizar")
    new_daily_budget_eur: float = Field(description="Nuevo presupuesto diario en euros")
    reason: str = Field(description="Razón del cambio")

TOOLS = [
    ObtenerAnunciosPorRendimientoInput,
    BuscarIdCampanaInput,
    EnviarAlertaSlackInput,
    ListarCampanasInput,
    GenerarReporteGoogleSlidesInput,
    GetAllCampaignsMetricsInput,
    GetCampaignRecommendationsInput,
    GetCampaignDetailsInput,
    UpdateAdsetBudgetInput,
]

# ========== SYSTEM INSTRUCTION ==========
SYSTEM_INSTRUCTION = f"""
Eres un agente experto en análisis de Meta Ads para la cuenta act_952835605437684.

🗺️ DESTINOS: Baqueira, Costa Blanca, Costa del Sol, Costa de la Luz, Ibiza, Menorca, Formentera, Cantabria

🚨 REGLAS CRÍTICAS:

1. **MEMORIA DE CONVERSACIÓN - PRIORIDAD MÁXIMA:**
   - 🔴 ANTES de responder, LEE TODO el historial de mensajes anteriores
   - Si el usuario pregunta sobre "eso", "esa campaña", "ese anuncio" → BUSCA en mensajes previos
   - Si ya mostraste datos de una campaña → NO la vuelvas a buscar, usa los datos previos
   - Para preguntas como "¿qué recomiendas para mejorar?" → Si ya hablaste de una campaña específica, asume que se refiere a ESA
   - NUNCA pidas aclaraciones si el contexto está en el historial
   
   Ejemplos de seguimiento:
   - Usuario: "dame TOP 3 de Baqueira" → Respondes con datos
   - Usuario: "¿qué recomiendas para mejorar el CPA?" → Asumes que habla de Baqueira (está en el historial)
   - Usuario: "para esa campaña" → Identificas cuál campaña mencionó antes

2. **FLUJO AUTOMÁTICO:**
   Cuando mencionen una campaña:
   ✅ PASO 1: BuscarIdCampanaInput(nombre_campana="...")
   ✅ PASO 2: Extraer 'id_campana' del JSON
   ✅ PASO 3: Usar el ID en la herramienta correspondiente
   ✅ PASO 4: Presentar resultados
   
   ❌ PROHIBIDO pedir al usuario el ID o confirmación

3. **FECHAS:**
   - "últimos 7 días" / "última semana" / "semana pasada" → date_preset: "last_7d"
   - "último mes" / "mes pasado" → date_preset: "last_month"
   - "este mes" → date_preset: "this_month"
   - "septiembre 2025" → date_start: "2025-09-01", date_end: "2025-09-30"
   - SIEMPRE formato YYYY-MM-DD
   - NO uses preset y fechas personalizadas juntos

4. **CONSULTAS GLOBALES:**
   Para preguntas sobre "todas las campañas" o "total":
   - "¿cuál fue el gasto total?" → GetAllCampaignsMetricsInput(date_preset="last_7d")
   - "¿cómo fue la semana pasada en Meta?" → GetAllCampaignsMetricsInput(date_preset="last_7d")
   - "CPA global de las campañas" → GetAllCampaignsMetricsInput(date_preset="last_7d", metrics=["cpa"])

5. **FORMATO DE RESPUESTA:**
   - Presentar SOLO datos de anuncios/campañas
   - NO incluir conocimiento base adicional
   - Formato claro con métricas destacadas
   - Usa emojis: 💰 (gasto), 👆 (clicks), 👁️ (impresiones), 🎯 (conversiones)

6. **SEGURIDAD:**
   - SOLO responder sobre Meta Ads y marketing digital
   - NO inventar métricas
   - Validar que campaign_ids existan

7. **🆕 RECOMENDACIONES Y DETALLES TÉCNICOS:**
   - "¿Qué puedo mejorar?" → BuscarIdCampanaInput + GetCampaignRecommendationsInput
   - "Estrategia de puja de Ibiza?" → GetCampaignDetailsInput
   - "¿Tiene Advantage+ activado?" → GetCampaignDetailsInput

8. **🆕 ACCIONES DE OPTIMIZACIÓN (FASE 2 - MODO MOCK):**
   - Solo si el usuario EXPLÍCITAMENTE pide acción
   - Validar new_daily_budget_eur >= 5.0
   - ⚠️ MODO MOCK - no ejecuta cambios reales

Fecha actual: {datetime.now().strftime('%Y-%m-%d')}
"""

# ========== INICIALIZACIÓN ==========
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    temperature=0.0,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)
llm_with_tools = llm.bind_tools(TOOLS)

print("✅ Conexión con Gemini API exitosa.")
print("🚀 Agente Inicializado (MODO UNIFICADO - Herramientas locales)")
print("-" * 50)

# ========== NODOS DEL GRAFO ==========
def call_llm(state: AgentState) -> Dict[str, Any]:
    """
    Nodo que llama al LLM con herramientas.
    """
    messages = state["messages"]
    
    # ✅ INYECTAR CONTEXTO DEL HISTORIAL
    # Si hay más de 2 mensajes (hay historial), crear un resumen
    if len(messages) > 2:
        # Extraer menciones de campañas del historial
        campaign_mentions = []
        for msg in messages[:-1]:  # Todos menos el último (query actual)
            content = str(msg.content) if hasattr(msg, 'content') else str(msg)
            # Buscar IDs de campaña en el historial
            if '"id_campana":' in content or 'campaña' in content.lower() or 'baqueira' in content.lower():
                campaign_mentions.append(content[:200])
        
        # Si encontramos menciones previas, agregarlas como contexto
        if campaign_mentions:
            context_msg = SystemMessage(
                content=f"""[CONTEXTO DE CONVERSACIÓN ANTERIOR]
El usuario ya habló sobre:
{chr(10).join(f"- {m}" for m in campaign_mentions[:3])}

IMPORTANTE: Si el usuario pregunta sobre "eso", "esa campaña", o hace seguimiento,
asume que se refiere a la información ya discutida arriba."""
            )
            messages = [context_msg] + messages
    
    # Agregar system message si no existe
    has_system_message = any(isinstance(msg, SystemMessage) for msg in messages)
    if not has_system_message:
        messages = [SystemMessage(content=SYSTEM_INSTRUCTION)] + messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def execute_tools(state: AgentState) -> Dict[str, Any]:
    """
    Ejecuta herramientas LOCALMENTE (sin HTTP requests)
    """
    # ✅ Importar herramientas locales
    from ..tools.ads import obtener_anuncios_por_rendimiento_func
    from ..tools.campaigns import buscar_id_campana_func, listar_campanas_func
    from ..tools.integrations import enviar_alerta_slack_func, generar_reporte_google_slides_func
    from ..tools.metrics import get_all_campaigns_metrics_func
    from ..tools.recommendations import get_campaign_recommendations_func, get_campaign_details_func
    from ..tools.actions import update_adset_budget_func
    
    from ..models.schemas import (
        ObtenerAnunciosPorRendimientoInput,
        BuscarIdCampanaInput,
        ListarCampanasInput,
        EnviarAlertaSlackInput,
        GenerarReporteGoogleSlidesInput,
        GetAllCampaignsMetricsInput,
        GetCampaignRecommendationsInput,
        GetCampaignDetailsInput,
        UpdateAdsetBudgetInput
    )
    
    # Mapeo de herramientas a funciones locales
    tool_function_map = {
        "ObtenerAnunciosPorRendimientoInput": (obtener_anuncios_por_rendimiento_func, ObtenerAnunciosPorRendimientoInput),
        "BuscarIdCampanaInput": (buscar_id_campana_func, BuscarIdCampanaInput),
        "ListarCampanasInput": (listar_campanas_func, ListarCampanasInput),
        "EnviarAlertaSlackInput": (enviar_alerta_slack_func, EnviarAlertaSlackInput),
        "GenerarReporteGoogleSlidesInput": (generar_reporte_google_slides_func, GenerarReporteGoogleSlidesInput),
        "GetAllCampaignsMetricsInput": (get_all_campaigns_metrics_func, GetAllCampaignsMetricsInput),
        "GetCampaignRecommendationsInput": (get_campaign_recommendations_func, GetCampaignRecommendationsInput),
        "GetCampaignDetailsInput": (get_campaign_details_func, GetCampaignDetailsInput),
        "UpdateAdsetBudgetInput": (update_adset_budget_func, UpdateAdsetBudgetInput),
    }
    
    last_message = state["messages"][-1]
    results = []
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {"messages": []}
    
    for tool_call in last_message.tool_calls:
        # Extraer información del tool_call
        if isinstance(tool_call, dict):
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args', {})
            tool_id = tool_call.get('id', str(uuid.uuid4()))
        else:
            tool_name = tool_call.name
            tool_args = tool_call.args
            tool_id = tool_call.id
        
        # Buscar la función correspondiente
        tool_info = tool_function_map.get(tool_name)
        
        if not tool_info:
            results.append(ToolMessage(
                content=f"Error: Herramienta {tool_name} no encontrada.",
                tool_call_id=tool_id
            ))
            continue
        
        tool_func, tool_input_class = tool_info
        
        try:
            # ✅ Crear el input Pydantic y llamar a la función LOCAL
            tool_input = tool_input_class(**tool_args)
            result = tool_func(tool_input)
            
            # Extraer el contenido según el tipo de resultado
            if hasattr(result, 'campanas_json'):
                result_content = result.campanas_json
            elif hasattr(result, 'datos_json'):
                result_content = result.datos_json
            elif hasattr(result, 'id_campana'):
                result_content = json.dumps({
                    "id_campana": result.id_campana,
                    "nombre_encontrado": result.nombre_encontrado
                })
            elif hasattr(result, 'slides_url'):
                result_content = result.slides_url
            elif hasattr(result, 'resultado'):
                result_content = result.resultado
            elif hasattr(result, 'message'):
                result_content = result.message
            else:
                result_content = str(result)
            
            results.append(ToolMessage(content=result_content, tool_call_id=tool_id))
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            results.append(ToolMessage(
                content=f"Error ejecutando {tool_name}: {str(e)}\n\nDetalle:\n{error_detail}",
                tool_call_id=tool_id
            ))
    
    return {"messages": results}


def should_continue(state: AgentState) -> str:
    """
    Decide si continuar ejecutando herramientas o terminar.
    """
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls'):
        if last_message.tool_calls and len(last_message.tool_calls) > 0:
            return "execute_tools"
    
    return "end"


# ========== CONSTRUCCIÓN DEL GRAFO ==========
workflow = StateGraph(AgentState)
workflow.add_node("call_llm", call_llm)
workflow.add_node("execute_tools", execute_tools)

workflow.set_entry_point("call_llm")
workflow.add_conditional_edges(
    "call_llm",
    should_continue,
    {"execute_tools": "execute_tools", "end": END}
)
workflow.add_edge("execute_tools", "call_llm")

# ========== COMPILACIÓN CON MEMORYSAVER ==========

print("\n" + "="*70)
print("🚀 Compilando agente con MemorySaver + LangSmith")
print("="*70)

# ✅ CRITICAL: MemorySaver para persistencia de conversaciones
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

print(f"✅ Agente compilado exitosamente")
print(f"🧠 Checkpointer: {type(app.checkpointer).__name__}")
print(f"🌐 LangSmith Project: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
print(f"📊 Tracing: {os.getenv('LANGCHAIN_TRACING_V2', 'false')}")
print(f"🎯 Versión: 3.4 MEMORIA + LangSmith")
print(f"🛠️ 9 herramientas: 8 consultas + 1 acción")
print("="*70 + "\n")


# ========== SCRIPT DE PRUEBA ==========
if __name__ == "__main__":
    print("\n🧪 Testing MemorySaver...\n")
    
    # Test básico de persistencia
    test_thread = "test_memory_001"
    
    print(f"📝 Creando conversación de prueba (thread: {test_thread})...")
    
    config = {"configurable": {"thread_id": test_thread}}
    
    # Mensaje 1
    print("\n🔵 TURNO 1:")
    result1 = app.invoke(
        {"messages": [HumanMessage(content="Hola, necesito ayuda con Meta Ads")]},
        config=config
    )
    print(f"   Mensajes en estado: {len(result1['messages'])}")
    print(f"   Última respuesta: {result1['messages'][-1].content[:100]}...")
    
    # Mensaje 2 (mismo thread - debe recordar)
    print("\n🔵 TURNO 2 (debe recordar el contexto):")
    result2 = app.invoke(
        {"messages": [HumanMessage(content="¿Qué me dijiste antes?")]},
        config=config
    )
    print(f"   Mensajes en estado: {len(result2['messages'])}")
    
    if len(result2['messages']) > 2:
        print(f"   ✅ MEMORIA FUNCIONA: {len(result2['messages'])} mensajes en historial")
    else:
        print(f"   ❌ MEMORIA NO FUNCIONA: Solo {len(result2['messages'])} mensajes")
    
    print("\n✅ Tests completados")