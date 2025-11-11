# streamlit_app.py - VERSIÓN FINAL CORREGIDA

import streamlit as st
import os
import uuid
from langgraph_agent.orchestrator_v3 import OrchestratorV3 
from dotenv import load_dotenv

load_dotenv()

# =======================================================
# CONFIGURACIÓN
# =======================================================

st.set_page_config(
    page_title="🤖 Agente de Meta Ads (V3.5 Local)", 
    layout="wide"
)
st.title("🤖 Agente Conversacional de Meta Ads")
st.caption("Con tecnología LangGraph + Gemini 2.5 Flash")

@st.cache_resource
def get_orchestrator():
    """Inicializa y cachea el OrchestratorV3."""
    try:
        return OrchestratorV3() 
    except Exception as e:
        st.error(f"Error al inicializar el Orquestador: {e}")
        st.stop()

orch = get_orchestrator()

# =======================================================
# ESTADO DE SESIÓN
# =======================================================

# User ID
if 'user_id' not in st.session_state:
    st.session_state.user_id = os.environ.get("DEFAULT_USER_ID", "vivla_tester_123")

# Historial de mensajes
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        {"role": "assistant", "content": f"Hola {st.session_state.user_id}, soy el Agente Meta Ads. ¿En qué puedo ayudarte hoy?"}
    )

# 🆕 CRÍTICO: Thread ID persistente para mantener contexto conversacional
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = f"streamlit_{uuid.uuid4().hex[:8]}"

# =======================================================
# FUNCIÓN AUXILIAR: EXTRAER TEXTO LIMPIO
# =======================================================

def extract_clean_text(content) -> str:
    """
    Extrae texto limpio de diferentes formatos de respuesta.
    
    Maneja:
    - Diccionarios de Gemini: {'type': 'text', 'text': '...', 'extras': {...}}
    - Strings directos
    - Listas de mensajes
    """
    # Caso 1: Dict con estructura de Gemini
    if isinstance(content, dict):
        if "text" in content:
            text = content["text"]
        elif "content" in content:
            text = content["content"]
        else:
            # Fallback: convertir a string pero sin 'extras'
            filtered_content = {k: v for k, v in content.items() if k != 'extras'}
            text = str(filtered_content)
    
    # Caso 2: Lista de mensajes
    elif isinstance(content, list):
        # Extraer texto de cada mensaje
        texts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            else:
                texts.append(str(item))
        text = "\n".join(texts)
    
    # Caso 3: String directo
    else:
        text = str(content)
    
    # Limpiar emojis de códigos
    text = (
        text.replace(":moneybag:", "💰")
            .replace(":point_up_2:", "👆")
            .replace(":eye:", "👁️")
            .replace(":dart:", "🎯")
            .replace(":chart_with_upwards_trend:", "📈")
            .replace(":fire:", "🔥")
            .replace(":bulb:", "💡")
            .replace(":warning:", "⚠️")
            .replace(":check_mark:", "✅")
            .replace(":rocket:", "🚀")
            .replace(":tada:", "🎉")
    )
    
    return text

# =======================================================
# INTERFAZ DE CHAT
# =======================================================

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # 🔧 CORRECCIÓN: Extraer texto limpio antes de mostrar
        clean_content = extract_clean_text(message["content"])
        st.markdown(clean_content)

# Input del usuario
if prompt := st.chat_input("Pregunta sobre tus campañas (ej. TOP 3 anuncios de Ibiza)"):
    
    # Añadir mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Procesar con el agente
    with st.chat_message("assistant"):
        with st.spinner('🤖 Analizando y procesando la consulta...'):
            try:
                # 🔧 CRÍTICO: Usar thread_id persistente para mantener contexto
                result = orch.process_query(
                    query=prompt,
                    thread_id=st.session_state.thread_id,  # ← Thread persistente
                    user_id=st.session_state.user_id
                )
                
                response_content = result.content
                tools_used = result.metadata.get('tools_used', [])

                # 🔧 CORRECCIÓN: Extraer texto limpio
                clean_text = extract_clean_text(response_content)
                
                # Mostrar respuesta limpia
                st.markdown(clean_text)
                
                # Mostrar herramientas usadas
                if tools_used:
                    tools_formatted = ', '.join([t.split('/')[-1] for t in tools_used])
                    st.caption(f"🔧 Herramientas usadas: {tools_formatted}")
                
                # 🔧 CORRECCIÓN: Guardar contenido limpio en el historial
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": clean_text  # ← Guardar texto limpio, no el dict
                })

            except Exception as e:
                error_message = f"❌ Ocurrió un error inesperado: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# =======================================================
# SIDEBAR: INFORMACIÓN Y CONTROLES
# =======================================================

with st.sidebar:
    st.header("ℹ️ Información de Sesión")
    st.write(f"**Usuario:** {st.session_state.user_id}")
    st.write(f"**Thread ID:** `{st.session_state.thread_id}`")  # ← Mostrar thread
    st.write(f"**Mensajes:** {len(st.session_state.messages)}")
    
    st.divider()
    
    # Botón para limpiar historial
    if st.button("🗑️ Nueva Conversación", use_container_width=True):
        st.session_state.messages = []
        # 🆕 IMPORTANTE: Generar nuevo thread_id al limpiar
        st.session_state.thread_id = f"streamlit_{uuid.uuid4().hex[:8]}"
        st.session_state.messages.append(
            {"role": "assistant", "content": f"Hola {st.session_state.user_id}, soy el Agente Meta Ads. ¿En qué puedo ayudarte hoy?"}
        )
        st.rerun()
    
    st.divider()
    
    # Información del sistema
    st.caption("**Meta Ads Agent v3.2**")
    st.caption("Powered by LangGraph + Gemini")
    st.caption("🔧 9 herramientas disponibles")
    
    # Ayuda rápida
    with st.expander("💡 Ejemplos de Consultas"):
        st.markdown("""
        **Consultas Básicas:**
        - `TOP 3 de Baqueira`
        - `lista todas las campañas`
        - `busca la campaña de Ibiza`
        
        **Análisis:**
        - `compara esta semana con la anterior`
        - `¿qué recomiendas para mejorar el CPA?`
        - `dame detalles de la campaña X`
        
        **Conversacional:**
        - `y para la campaña de Menorca?`
        - `optimiza automáticamente`
        """)