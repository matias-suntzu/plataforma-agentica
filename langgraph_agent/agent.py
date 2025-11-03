import os
import json
import uuid
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime, timedelta

# LangGraph y LangChain components
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_core.messages import ToolCall
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
from pydantic import BaseModel, Field


# Importar RAG y Memory Managers
from rag_manager import RAGManager
from memory_manager import MemoryManager

load_dotenv()

# --- 1. CONFIGURACIÓN DEL SERVIDOR DE HERRAMIENTAS Y LLM ---

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "meta-ads-agent"

LANGSERVE_URL = os.getenv("TOOL_SERVER_BASE_URL", "http://localhost:8000")
TOOL_API_KEY = "53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG"

if not TOOL_API_KEY or not LANGSERVE_URL:
    raise ValueError("Faltan variables de entorno TOOL_SERVER_API_KEY o TOOL_SERVER_BASE_URL.")
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("Falta la variable de entorno GEMINI_API_KEY.")

GEMINI_MODEL = "gemini-2.5-flash"

from datetime import datetime
import calendar

def parse_month_to_dates(month_str: str, year: int = None) -> tuple:
    """
    Convierte un mes en español a fechas de inicio y fin.
    
    Args:
        month_str: Nombre del mes (ej: "septiembre", "sep")
        year: Año (default: año actual)
    
    Returns:
        tuple: (date_start, date_end) en formato YYYY-MM-DD
    """
    if year is None:
        year = datetime.now().year
    
    months_map = {
        'enero': 1, 'ene': 1,
        'febrero': 2, 'feb': 2,
        'marzo': 3, 'mar': 3,
        'abril': 4, 'abr': 4,
        'mayo': 5, 'may': 5,
        'junio': 6, 'jun': 6,
        'julio': 7, 'jul': 7,
        'agosto': 8, 'ago': 8,
        'septiembre': 9, 'sep': 9, 'sept': 9,
        'octubre': 10, 'oct': 10,
        'noviembre': 11, 'nov': 11,
        'diciembre': 12, 'dic': 12
    }
    
    month_num = months_map.get(month_str.lower())
    if not month_num:
        return None, None
    
    # Obtener último día del mes
    last_day = calendar.monthrange(year, month_num)[1]
    
    date_start = f"{year}-{month_num:02d}-01"
    date_end = f"{year}-{month_num:02d}-{last_day}"
    
    return date_start, date_end

# --- 2. DEFINICIÓN DEL ESTADO DEL AGENTE ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]

# --- 3. ESQUEMAS REMOTOS PARA EL LLM ---

class ObtenerAnunciosPorRendimientoInput(BaseModel):
    """
    Obtiene el TOP de anuncios de una campaña por rendimiento con métricas reales.
    
    IMPORTANTE: 
    - Requiere el campana_id. Si solo tienes el nombre, usa BuscarIdCampanaInput primero.
    - Soporta tanto date_preset como rangos personalizados (date_start/date_end).
    """
    campana_id: str = Field(description="ID único de la campaña de Meta Ads.")
    
    # Opción 1: Usar presets
    date_preset: Optional[str] = Field(
        default=None,  # ← CAMBIAR de "last_7d" a None
        description="Periodo preset: 'last_7d', 'last_month', 'this_month', 'today', 'yesterday', 'lifetime'"
    )
    
    # Opción 2: Usar fechas personalizadas
    date_start: Optional[str] = Field(
        default=None,
        description="Fecha de inicio en formato YYYY-MM-DD (ej: '2025-09-01'). Usar junto con date_end."
    )
    date_end: Optional[str] = Field(
        default=None,
        description="Fecha de fin en formato YYYY-MM-DD (ej: '2025-09-30'). Usar junto con date_start."
    )
    
    limite: int = Field(
        default=3,
        description="Número máximo de anuncios a devolver (TOP N)"
    )

class BuscarIdCampanaInput(BaseModel):
    """
    HERRAMIENTA OBLIGATORIA: Usa esta herramienta PRIMERO cuando el usuario mencione un nombre de campaña sin proporcionar su ID.
    Busca el ID de una campaña por nombre (búsqueda parcial).
    Retorna un JSON con 'id_campana' y 'nombre_encontrado'.
    """
    nombre_campana: str = Field(description="Nombre o parte del nombre de la campaña a buscar. Ej: 'baqueira', 'costa', 'verano'")

class EnviarAlertaSlackInput(BaseModel):
    """Envía un mensaje o alerta crítica a un canal de Slack."""
    mensaje: str = Field(description="Mensaje completo y conciso a enviar a Slack.")

class ListarCampanasInput(BaseModel):
    """Lista las campañas más recientes y activas de la cuenta de anuncios."""
    limite: int = Field(default=20, description="Máximo número de campañas a listar.")

class GenerarReporteGoogleSlidesInput(BaseModel):
    """Genera un reporte visual en Google Slides con los datos de rendimiento."""
    resumen_ejecutivo: str = Field(description="Resumen ejecutivo del análisis de anuncios.")
    datos_tabla_json: str = Field(description="Datos JSON de los anuncios obtenidos anteriormente.")

class GetAllCampaignsMetricsInput(BaseModel):
    """Obtiene métricas agregadas de TODAS las campañas"""
    date_preset: str = Field(default="last_30d")
    metrics: List[str] = Field(default=["spend", "clicks", "ctr", "cpm", "cpc"])

class ComparePeriodsInput(BaseModel):
    """Compara métricas entre dos períodos"""
    period1: str = Field(description="Ej: 'last_month'")
    period2: str = Field(description="Ej: 'this_month'")
    campaigns: Optional[List[str]] = None  # Si es null, compara todas

class DetectAnomaliesInput(BaseModel):
    """Detecta anomalías en campañas activas"""
    threshold_cpc: float = Field(default=10.0)
    threshold_cpa: float = Field(default=50.0)
    min_spend: float = Field(default=100.0)

TOOLS = [
    ObtenerAnunciosPorRendimientoInput,
    BuscarIdCampanaInput,
    EnviarAlertaSlackInput,
    ListarCampanasInput,
    GenerarReporteGoogleSlidesInput,
    GetAllCampaignsMetricsInput,
    ComparePeriodsInput,
    DetectAnomaliesInput,
]

# 🔥 SYSTEM INSTRUCTION MEJORADO - MÁS EXPLÍCITO CON MEMORIA DE CONVERSACIÓN
SYSTEM_INSTRUCTION = f"""
Eres un agente experto en análisis de Meta Ads para la cuenta act_952835605437684.

📍 DESTINOS DISPONIBLES:
Los anuncios están organizados por destinos turísticos:
- Baqueira (estación de ski)
- Costa Blanca
- Costa del Sol
- Costa de la Luz
- Ibiza
- Menorca
- Formentera
- Cantabria

Cuando un usuario mencione un destino (ej: "Costa Blanca", "Ibiza"), búscalo automáticamente.

🚨 REGLAS CRÍTICAS - EJECUTAR SIEMPRE AUTOMÁTICAMENTE:

1. **USO DE MEMORIA DE CONVERSACIÓN:**
   
   ✅ SIEMPRE revisa el historial de mensajes de la conversación actual
   ✅ Si el usuario hace preguntas de seguimiento (ej: "¿cuál tiene mejor CPA?", "¿y el segundo?"), 
      usa el contexto de tus respuestas anteriores en ESTE MISMO THREAD
   ✅ NO pidas información que ya proporcionaste en mensajes anteriores
   
   Ejemplo:
   Usuario: "Dame el TOP 3 de anuncios de Baqueira"
   Tú: [Presentas 3 anuncios con sus métricas]
   Usuario: "¿Cuál tiene mejor CPA?"
   Tú: [Respondes basándote en los datos que YA MOSTRASTE, NO vuelvas a buscar]

2. **FLUJO AUTOMÁTICO OBLIGATORIO (NO PREGUNTAR AL USUARIO):**
   
   Cuando el usuario mencione CUALQUIER campaña por nombre (ej: "baqueira", "costa blanca", "tenerife"):
   
   ✅ PASO 1: Llamar INMEDIATAMENTE a BuscarIdCampanaInput(nombre_campana="...")
   ✅ PASO 2: Parsear el JSON de respuesta y extraer 'id_campana'
   ✅ PASO 3: Llamar INMEDIATAMENTE a ObtenerAnunciosPorRendimientoInput(campana_id=..., date_preset=..., limite=3)
   ✅ PASO 4: Presentar los resultados al usuario
   
   ❌ PROHIBIDO:
   - Pedir al usuario que proporcione el ID de campaña
   - Preguntar si quieres buscar la campaña
   - Pedir confirmación antes de ejecutar las herramientas
   - Detener el flujo en cualquier punto
   - Pedir información que ya tienes en el historial de la conversación

3. **MAPEO DE PERIODOS Y FECHAS:**

   A) PRESETS (usar cuando el usuario diga "último", "este", etc.):
   - "últimos 7 días" / "última semana" → date_preset: "last_7d"
   - "último mes" / "mes pasado" → date_preset: "last_month"  
   - "este mes" / "mes actual" → date_preset: "this_month"
   - "hoy" → date_preset: "today"
   - "ayer" → date_preset: "yesterday"
   - "desde el inicio" / "histórico" → date_preset: "lifetime"
   
   B) FECHAS PERSONALIZADAS (cuando el usuario mencione meses/años específicos):
   - "septiembre de 2025" → date_start: "2025-09-01", date_end: "2025-09-30"
   - "agosto 2025" → date_start: "2025-08-01", date_end: "2025-08-31"
   - "primer trimestre 2025" → date_start: "2025-01-01", date_end: "2025-03-31"
   - "del 1 al 15 de octubre" → date_start: "2025-10-01", date_end: "2025-10-15"
   
   📅 REGLAS DE FECHAS:
   - SIEMPRE usar formato YYYY-MM-DD para date_start y date_end
   - Si el usuario no especifica año, usar el año actual (2025)
   - Si menciona un mes específico, usar el primer y último día de ese mes
   - NO uses date_preset y date_start/date_end al mismo tiempo
   - PRIORIZA fechas personalizadas si el usuario es específico

4. **FORMATO DE RESPUESTA FINAL:**
   - Cuando muestres totales de gastos, usa formato claro: "X€" o "X euros"
   - Para preguntas de gasto total, menciona PRIMERO el total y LUEGO el desglose
   - Ejemplo: "Se gastaron 1,234.56€ en Ibiza en septiembre de 2025. Aquí el TOP 3..."
   - Presentar SOLO los datos de los anuncios
   - NO incluir información adicional de conocimiento base
   - Formato claro con bullets y métricas destacadas
   - Incluir: Clicks, Impresiones, Gasto, CTR, CPM, CPC, Conversiones, CPA

5. **EJEMPLOS DE EJECUCIÓN CORRECTA:**

**Ejemplo A - Primera consulta:**
Usuario: "Dame el TOP 3 de anuncios de Baqueira del last_7d"
TÚ (sin preguntar nada):
→ BuscarIdCampanaInput(nombre_campana="baqueira")
→ ObtenerAnunciosPorRendimientoInput(campana_id="...", date_preset="last_7d", limite=3)
→ [Presentas resultados]

**Ejemplo B - Pregunta de seguimiento:**
Usuario: "¿Cuál tiene mejor CPA?"
TÚ (revisas tu respuesta anterior en el historial):
→ NO LLAMAS A NINGUNA HERRAMIENTA
→ Respondes directamente: "El anuncio X tiene el mejor CPA de Y€"

**Ejemplo C - Segunda pregunta de seguimiento:**
Usuario: "¿Y el segundo mejor CPA?"
TÚ (revisas tu respuesta anterior):
→ NO LLAMAS A NINGUNA HERRAMIENTA
→ Respondes directamente: "El segundo mejor CPA es del anuncio Z con W€"

6. **CONOCIMIENTO BASE:**
   - Tienes acceso a contexto adicional sobre Vivla y métricas
   - SOLO úsalo si el usuario pregunta explícitamente sobre esos temas
   - Para consultas de rendimiento de anuncios, IGNORA el contexto adicional
   - Responde SOLO con los datos de las herramientas

Fecha actual: {datetime.now().strftime('%Y-%m-%d')}

🚨 REGLAS DE SEGURIDAD:

1. **SCOPE RESTRINGIDO:**
   - SOLO responde preguntas sobre Meta Ads y marketing digital
   - Si preguntan sobre política, religión, temas personales → "No puedo ayudarte con eso"
   
2. **VALIDACIÓN DE DATOS:**
   - Verifica que los campaign_ids existan antes de consultar
   - Si no encuentras datos, di "No encontré esa campaña" (no inventes)
   
3. **PROHIBIDO:**
   - Inventar métricas o números
   - Responder preguntas fuera del dominio de Meta Ads
   - Dar consejos médicos, legales o financieros personales
"""

# Inicialización del LLM
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    temperature=0.0,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# Vincular las herramientas al LLM
llm_with_tools = llm.bind_tools(TOOLS)

# Inicializar RAG Manager
print("📄 Inicializando base de conocimiento (RAG)...")
rag_manager = RAGManager()
try:
    rag_manager.create_vectorstore()
    print("✅ Base de conocimiento cargada exitosamente")
except Exception as e:
    print(f"⚠️ Advertencia: No se pudo cargar la base de conocimiento: {e}")
    rag_manager = None

# Inicializar Memory Manager
print("📄 Inicializando gestor de memoria...")
memory_manager = MemoryManager()
print("✅ Gestor de memoria inicializado")

print("✅ Conexión con Gemini API exitosa.")
print(f"🚀 Agente Inicializado (Conexión LangServe: {LANGSERVE_URL})")
print("-" * 50)

# --- 4. NÓDULOS Y FUNCIONES DE ASISTENCIA ---

def call_llm(state: AgentState) -> Dict[str, Any]:
    """Invoca al LLM para generar una respuesta o llamadas a herramientas."""
    messages = state["messages"]
    
    # 🔍 DEBUG: Mostrar cuántos mensajes hay en el estado
    print(f"\n🔍 DEBUG call_llm: Total mensajes en estado: {len(messages)}")
    for i, msg in enumerate(messages):
        msg_type = type(msg).__name__
        content_preview = str(msg.content)[:100] if hasattr(msg, 'content') else 'N/A'
        print(f"   Mensaje {i}: {msg_type} - {content_preview}...")
    
    # 🔥 CAMBIO: Con SqliteSaver, los mensajes previos se recuperan automáticamente
    # Solo verificamos si necesitamos agregar el system message
    
    has_system_message = any(isinstance(msg, SystemMessage) for msg in messages)
    
    if not has_system_message:
        messages = [SystemMessage(content=SYSTEM_INSTRUCTION)] + messages
        print("✅ System instruction agregada")
    
    # 🔥 Contexto RAG solo para preguntas sobre Vivla/definiciones
    last_human_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_message = msg.content.lower()
            break
    
    add_context = False
    if last_human_message:
        context_keywords = ["qué es vivla", "cómo funciona", "definición", "qué significa", "explica"]
        performance_keywords = ["anuncios", "top", "campaña", "rendimiento", "clicks", "cpa", "ctr", "baqueira", "costa", "mejor", "segundo", "primero", "peor"]
        
        if any(keyword in last_human_message for keyword in context_keywords):
            add_context = True
        elif any(keyword in last_human_message for keyword in performance_keywords):
            add_context = False
    
    additional_context = []
    
    if add_context:
        if rag_manager and last_human_message:
            try:
                context = rag_manager.get_context_for_query(last_human_message, k=2)
                if context and "No se encontró información relevante" not in context:
                    additional_context.append(f"[CONOCIMIENTO BASE]\n{context}")
                    print(f"📚 Contexto RAG agregado")
            except Exception as e:
                print(f"⚠️ Error al obtener contexto RAG: {e}")
    
    if additional_context:
        context_message = AIMessage(content="\n\n".join(additional_context))
        messages = messages + [context_message]
    
    response = llm_with_tools.invoke(messages)
    
    print(f"\n--- DEBUG: LLM Response Type: {type(response)} ---")
    if hasattr(response, 'tool_calls'):
        print(f"--- Tool Calls: {len(response.tool_calls) if response.tool_calls else 0} ---")
        if response.tool_calls:
            for i, tc in enumerate(response.tool_calls):
                print(f"  Tool {i+1}: {tc.name if hasattr(tc, 'name') else tc.get('name', 'UNKNOWN')}")
    
    return {"messages": [response]}


def execute_tools(state: AgentState) -> Dict[str, Any]:
    """Ejecuta las herramientas llamadas por el LLM."""
    
    tool_map = {
        "ObtenerAnunciosPorRendimientoInput": f"{LANGSERVE_URL}/obteneranunciosrendimiento/invoke",
        "BuscarIdCampanaInput": f"{LANGSERVE_URL}/buscaridcampana/invoke",
        "EnviarAlertaSlackInput": f"{LANGSERVE_URL}/enviaralertaslack/invoke",
        "ListarCampanasInput": f"{LANGSERVE_URL}/listarcampanas/invoke",
        "GenerarReporteGoogleSlidesInput": f"{LANGSERVE_URL}/generar_reporte_slides/invoke",
    }
    
    last_message = state["messages"][-1]
    results = []
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        print("--- WARNING: execute_tools llamado sin tool_calls ---")
        return {"messages": []}
    
    tool_calls_list = last_message.tool_calls
    
    for tool_call in tool_calls_list:
        if isinstance(tool_call, dict):
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args', {})
            tool_id = tool_call.get('id', str(uuid.uuid4()))
        else:
            tool_name = tool_call.name
            tool_args = tool_call.args
            tool_id = tool_call.id
        
        tool_url = tool_map.get(tool_name)
        
        print(f"\n--- Ejecutando herramienta: {tool_name} ---")
        print(f"--- Args: {tool_args} ---")
        
        if not tool_url:
            error_content = f"Error: La herramienta {tool_name} no está mapeada."
            results.append(ToolMessage(content=error_content, tool_call_id=tool_id))
            continue
        
        try:
            headers = {"Content-Type": "application/json", "X-Tool-Api-Key": TOOL_API_KEY}
            response = requests.post(tool_url, headers=headers, json={"input": tool_args}, timeout=30)
            
            if response.status_code == 200:
                result_content = response.json().get('output', 'Error: Respuesta de herramienta vacía.')
                print(f"--- Resultado exitoso de {tool_name} ---")
                print(f"--- Content preview: {str(result_content)[:200]}... ---")
            else:
                error_detail = response.json().get('detail', 'Sin detalle de error.')
                result_content = f"Error al ejecutar la herramienta {tool_name}: Código {response.status_code}. Detalle: {error_detail}"
                print(f"--- ERROR: {result_content} ---")
            
            results.append(ToolMessage(content=str(result_content), tool_call_id=tool_id))
        
        except requests.exceptions.RequestException as e:
            error_content = f"Error al ejecutar {tool_name} remotamente: Fallo HTTP o Conexión. Error: {str(e)}"
            print(f"--- ERROR HTTP: {error_content} ---")
            results.append(ToolMessage(content=error_content, tool_call_id=tool_id))
        
        except Exception as e:
            error_content = f"Error al ejecutar {tool_name} remotamente: {str(e)}"
            print(f"--- ERROR GENERAL: {error_content} ---")
            results.append(ToolMessage(content=error_content, tool_call_id=tool_id))
    
    return {"messages": results}


def should_continue(state: AgentState) -> str:
    """Define la lógica de enrutamiento."""
    last_message = state["messages"][-1]
    
    print(f"\n--- DEBUG should_continue: Message type: {type(last_message)} ---")
    
    if hasattr(last_message, 'tool_calls'):
        has_calls = last_message.tool_calls and len(last_message.tool_calls) > 0
        print(f"--- Has tool_calls: {has_calls} ---")
        if has_calls:
            return "execute_tools"
    
    print("--- Routing to: end ---")
    return "end"


# --- 5. CONSTRUCCIÓN DEL GRAFO CON MEMORIA A CORTO PLAZO ---

# 🔥 CAMBIO CRÍTICO: Usar SqliteSaver en lugar de MemorySaver
# SqliteSaver persiste la memoria en disco entre reinicios del bot
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# Crear directorio para checkpoints si no existe
checkpoint_dir = Path("knowledge_base/checkpoints")
checkpoint_dir.mkdir(parents=True, exist_ok=True)

# Inicializar SqliteSaver correctamente
checkpoint_path = str(checkpoint_dir / "agent_memory.db")

# Crear conexión SQLite
conn = sqlite3.connect(checkpoint_path, check_same_thread=False)

# Inicializar SqliteSaver con la conexión
memory = SqliteSaver(conn)

print(f"✅ SqliteSaver inicializado (memoria a corto plazo persistente)")
print(f"📁 Checkpoint DB: {checkpoint_path}")

workflow = StateGraph(AgentState)
workflow.add_node("call_llm", call_llm)
workflow.add_node("execute_tools", execute_tools)

workflow.set_entry_point("call_llm")

workflow.add_conditional_edges(
    "call_llm",
    should_continue,
    {
        "execute_tools": "execute_tools",
        "end": END
    },
)

workflow.add_edge("execute_tools", "call_llm")

# 🔥 COMPILAR SEGÚN EL ENTORNO
if os.getenv("LANGGRAPH_API_URL") or os.getenv("LANGGRAPH_CLOUD"):
    # Ejecutándose en LangGraph Studio/Cloud
    app = workflow.compile()
    print("✅ Grafo compilado para LangGraph Studio (persistencia automática)")
else:
    # Ejecutándose localmente
    from langgraph.checkpoint.sqlite import SqliteSaver
    import sqlite3
    
    checkpoint_dir = Path("knowledge_base/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = str(checkpoint_dir / "agent_memory.db")
    conn = sqlite3.connect(checkpoint_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    app = workflow.compile(checkpointer=memory)
    print(f"✅ SqliteSaver inicializado (memoria a corto plazo persistente)")
    print(f"📁 Checkpoint DB: {checkpoint_path}")