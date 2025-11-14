"""
Agente Principal de Meta Ads con LangGraph
Versión: 3.3 (Con LangSmith)
"""

import os
import json
import uuid
from datetime import datetime
import calendar

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, List, Dict, Any, Optional

from dotenv import load_dotenv

from ..memory.rag_manager import RAGManager
from ..memory.memory_manager import MemoryManager

load_dotenv()

# ========== CONFIGURACIÓN ==========
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "meta-ads-agent"

#LANGSERVE_URL = os.getenv("TOOL_SERVER_BASE_URL", "http://localhost:8000")
GEMINI_MODEL = "gemini-2.5-flash"

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("Falta GEMINI_API_KEY")

# Verificar LangSmith (opcional, solo para logs)
if os.getenv("LANGSMITH_API_KEY"):
    print("✅ LangSmith configurado")
else:
    print("⚠️  LangSmith no configurado (continúa sin tracing)")

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

🏖️ DESTINOS: Baqueira, Costa Blanca, Costa del Sol, Costa de la Luz, Ibiza, Menorca, Formentera, Cantabria

🚨 REGLAS CRÍTICAS:

1. **MEMORIA DE CONVERSACIÓN:**
   - SIEMPRE revisa el historial de mensajes
   - Para preguntas de seguimiento (ej: "¿cuál tiene mejor CPA?"), usa datos previos
   - NO re-busques información que ya mostraste

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

# RAG Manager
print("📄 Inicializando base de conocimiento (RAG)...")
rag_manager = RAGManager()
try:
    rag_manager.create_vectorstore()
    print("✅ Base de conocimiento cargada exitosamente")
except Exception as e:
    print(f"⚠️ Advertencia: RAG no disponible: {e}")
    rag_manager = None

# Memory Manager
print("📄 Inicializando gestor de memoria...")
memory_manager = MemoryManager()
print("✅ Gestor de memoria inicializado")

print("✅ Conexión con Gemini API exitosa.")
print("🚀 Agente Inicializado (MODO UNIFICADO - Herramientas locales)")
print("-" * 50)

# ========== NODOS DEL GRAFO ==========
def call_llm(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]
    
    has_system_message = any(isinstance(msg, SystemMessage) for msg in messages)
    if not has_system_message:
        messages = [SystemMessage(content=SYSTEM_INSTRUCTION)] + messages
    
    last_human_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_message = msg.content.lower()
            break
    
    add_context = False
    if last_human_message and rag_manager:
        context_keywords = ["qué es vivla", "cómo funciona", "definición", "explica", "advantage"]
        performance_keywords = ["anuncios", "top", "campaña", "rendimiento", "clicks", "cpa", "ctr"]
        
        if any(kw in last_human_message for kw in context_keywords):
            add_context = True
        elif any(kw in last_human_message for kw in performance_keywords):
            add_context = False
    
    if add_context and rag_manager:
        try:
            context = rag_manager.get_context_for_query(last_human_message, k=2)
            if context and "No se encontró" not in context:
                context_message = AIMessage(content=f"[CONOCIMIENTO BASE]\n{context}")
                messages = messages + [context_message]
        except Exception:
            pass
    
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

# ========== COMPILACIÓN CON LANGSMITH ==========

print("\n" + "="*70)
print("🚀 Compilando agente con LangSmith")
print("="*70)

# ✅ LangSmith maneja automáticamente:
# - Checkpointing (persistencia)
# - Tracing (observabilidad)
# - Memory (estados conversacionales)
# - Time-travel (debugging)

app = workflow.compile()

print(f"✅ Agente compilado exitosamente")
print(f"🌐 LangSmith Project: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
print(f"📊 Tracing: {os.getenv('LANGCHAIN_TRACING_V2', 'false')}")
print(f"🎯 Versión: 3.2 FASE 2 + LangSmith")
print(f"🛠️ 9 herramientas: 8 consultas + 1 acción")
print("="*70 + "\n")


# ========== SCRIPT DE PRUEBA ==========
if __name__ == "__main__":
    print("\n🧪 Testing SQLite Checkpointer...\n")
    
    # Mostrar estadísticas iniciales
    print_checkpoint_stats()
    
    # Test básico de persistencia
    test_thread = "test_checkpoint_001"
    
    print(f"🔍 Creando conversación de prueba (thread: {test_thread})...")
    
    config = RunnableConfig(configurable={"thread_id": test_thread})
    
    # Mensaje 1
    result1 = app.invoke(
        {"messages": [HumanMessage(content="Hola, soy una prueba de checkpoints")]},
        config=config
    )
    print("✅ Checkpoint 1 creado")
    
    # Mensaje 2
    result2 = app.invoke(
        {"messages": [HumanMessage(content="Lista todas las campañas")]},
        config=config
    )
    print("✅ Checkpoint 2 creado")
    
    # Obtener historial
    print(f"\n📜 Historial de checkpoints para {test_thread}:")
    history = get_checkpoint_history(test_thread)
    
    for i, cp in enumerate(history, 1):
        print(f"   {i}. Checkpoint ID: {cp['checkpoint_id']}")
        print(f"      Parent: {cp['parent_checkpoint_id']}")
    
    # Estadísticas finales
    print_checkpoint_stats()
    
    print("✅ Tests completados")

    