import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain_core.messages import HumanMessage
from tool_server_api.tools.integrations import enviar_alerta_slack_func

# Importar el agente y gestores
from langgraph_agent.agent import app as agent_app, memory_manager

load_dotenv()

# Inicializar Slack App
slack_app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

print("⚡️ Bot de Slack iniciado en modo SocketMode...")


def get_thread_id(channel_id: str, thread_ts: str = None) -> str:
    """
    Genera un thread_id único para mantener el contexto de conversación.
    
    Args:
        channel_id: ID del canal de Slack
        thread_ts: Timestamp del thread (si existe)
        
    Returns:
        Thread ID único para esta conversación
    """
    # Si hay thread, usar ese ID; si no, usar el canal
    if thread_ts:
        return f"{channel_id}_{thread_ts}"
    return f"{channel_id}_main"


@slack_app.message(".*")
def handle_message(message, say):
    """
    Maneja todos los mensajes que mencionen al bot.
    """
    user_message = message.get("text", "")
    channel_id = message.get("channel", "")
    thread_ts = message.get("thread_ts") or message.get("ts")
    user_id = message.get("user", "")
    
    # Ignorar mensajes del propio bot
    if message.get("bot_id"):
        return
    
    print(f"🤖 Agente procesando mensaje: '{user_message}'")
    
    # Generar thread_id para memoria
    thread_id = get_thread_id(channel_id, thread_ts)
    print(f"🔑 Thread ID generado: {thread_id}")
    
    # Notificar al usuario que estamos procesando
    say(
        text=f"Recibí tu pregunta sobre Meta Ads: '{user_message}'. Dame un momento para consultar al agente...",
        thread_ts=thread_ts
    )
    
    try:
        # Configuración para invocar el agente con memoria
        # IMPORTANTE: El config DEBE tener thread_id en configurable
        config = {
            "configurable": {
                "thread_id": str(thread_id)  # Asegurar que sea string
            }
        }
        
        print(f"🔧 Config: {config}")
        
        # Crear mensaje de entrada
        input_message = {
            "messages": [HumanMessage(content=user_message)]
        }
        
        # Invocar el agente CON memoria a corto plazo
        print("📤 Invocando agente con memoria...")
        result = agent_app.invoke(input_message, config=config)
        print(f"📥 Resultado recibido. Tipo: {type(result)}")
        
        # Extraer respuesta de forma robusta
        agent_response = None
        
        # Intentar extraer del resultado
        if isinstance(result, dict):
            messages = result.get("messages", [])
            print(f"🔍 Mensajes encontrados: {len(messages)}")
            
            if messages:
                last_message = messages[-1]
                print(f"🔍 Tipo del último mensaje: {type(last_message)}")
                
                if hasattr(last_message, "content"):
                    content = last_message.content
                    print(f"🔍 Tipo de content: {type(content)}")
                    
                    # Si el content es una lista, convertirlo a string
                    if isinstance(content, list):
                        # Extraer texto de cada elemento
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict):
                                text_parts.append(item.get("text", str(item)))
                            elif isinstance(item, str):
                                text_parts.append(item)
                            else:
                                text_parts.append(str(item))
                        agent_response = "\n".join(text_parts)
                    else:
                        agent_response = str(content)
                        
                elif isinstance(last_message, dict):
                    agent_response = last_message.get("content")
        
        # Si logramos extraer la respuesta
        if agent_response and len(agent_response) > 1:
            print(f"✅ Respuesta extraída ({len(agent_response)} caracteres)")
            print(f"📝 Preview: {agent_response[:200]}...")
            
            # Enviar respuesta a Slack
            say(text=agent_response, thread_ts=thread_ts)

            # Extraer y guardar aprendizajes automáticos
            extract_and_save_learnings(user_message, agent_response, thread_id)

            # 💾 GUARDAR EN MEMORIA A LARGO PLAZO
            try:
                # Extraer metadata relevante
                metadata = {
                    "channel_id": channel_id,
                    "user_id": user_id,
                    "thread_ts": thread_ts
                }

                # Detectar si se mencionaron campañas
                if "campaña" in user_message.lower() or "campaign" in user_message.lower() or "baqueira" in user_message.lower() or "costa" in user_message.lower():
                    metadata["related_campaign"] = True
                
                # Detectar tipo de consulta
                if "cpa" in user_message.lower() or "ctr" in user_message.lower() or "roas" in user_message.lower():
                     metadata["mentions_metrics"] = True
            
                if "mejor" in user_message.lower() or "top" in user_message.lower():
                     metadata["improvement_query"] = True
            
                # Guardar conversación
                print("💾 Guardando conversación en memoria a largo plazo...")
                memory_manager.save_conversation(
                    thread_id=thread_id,
                    user_message=user_message,
                    agent_response=agent_response,
                    metadata=metadata
                )

                print(f"✅ Conversación guardada en memoria a largo plazo (thread: {thread_id})")
            
            except Exception as mem_error:
                print(f"❌ Error guardando en memoria a largo plazo: {str(mem_error)}")
                import traceback
                print(traceback.format_exc())
            
            print("✅ Agente ha respondido con texto.")
        else:
            error_msg = "Lo siento, no pude procesar tu solicitud correctamente."
            say(text=error_msg, thread_ts=thread_ts)
            print(f"❌ Respuesta vacía o inválida. Content: {agent_response}")
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = f"Lo siento, ocurrió un error al procesar tu solicitud: {str(e)}"
        say(text=error_msg, thread_ts=thread_ts)
        print(f"❌ Error completo:\n{error_trace}")

@slack_app.event("app_mention")
def handle_mention(event, say):
    """
    Maneja cuando el bot es mencionado directamente.
    """
    user_message = event.get("text", "")
    channel_id = event.get("channel", "")
    thread_ts = event.get("thread_ts") or event.get("ts")
    
    # Remover la mención del bot del mensaje
    user_message = user_message.split(">", 1)[-1].strip()
    
    # Crear diccionario de mensaje para procesar
    message_dict = {
        "text": user_message,
        "channel": channel_id,
        "thread_ts": thread_ts,
        "ts": event.get("ts"),
        "user": event.get("user")
    }
    
    # Procesar como mensaje normal
    handle_message(message_dict, say)


# Comando para ver estadísticas de memoria
@slack_app.command("/memoria_stats")
def handle_memory_stats(ack, say, command):
    """Muestra estadísticas de la memoria del agente."""
    ack()
    
    try:
        stats = memory_manager.get_statistics()
        
        response = f"""📊 *Estadísticas de Memoria del Agente*
        
💬 Conversaciones guardadas: {stats['conversations']}
🧠 Aprendizajes acumulados: {stats['learnings']}

La memoria permite al agente:
- Recordar conversaciones anteriores
- Aprender de patrones exitosos
- Mejorar recomendaciones con el tiempo
"""
        say(response)
    
    except Exception as e:
        say(f"❌ Error obteniendo estadísticas: {str(e)}")


# Comando para guardar feedback
@slack_app.command("/feedback")
def handle_feedback(ack, say, command):
    """
    Guarda feedback del usuario sobre el agente.
    Uso: /feedback [positivo|negativo] [descripción]
    """
    ack()
    
    text = command.get("text", "")
    parts = text.split(" ", 1)
    
    if len(parts) < 2:
        say("❌ Uso: `/feedback positivo|negativo [tu comentario]`")
        return
    
    feedback_type = parts[0].lower()
    feedback_text = parts[1]
    
    if feedback_type not in ["positivo", "negativo"]:
        say("❌ El tipo debe ser 'positivo' o 'negativo'")
        return
    
    try:
        # Guardar como aprendizaje
        memory_manager.save_learning(
            learning_type="user_feedback",
            description=f"Feedback {feedback_type} del usuario",
            context=f"Usuario en Slack proporcionó feedback: {feedback_text}",
            recommendation=f"Considerar este feedback para futuras interacciones",
            metadata={"feedback_type": feedback_type, "user_id": command.get("user_id")}
        )
        
        say(f"✅ Gracias por tu feedback {feedback_type}. Lo he registrado para mejorar.")
    
    except Exception as e:
        say(f"❌ Error guardando feedback: {str(e)}")

def extract_and_save_learnings(user_message: str, agent_response: str, thread_id: str):
    """
    Extrae y guarda aprendizajes automáticamente de conversaciones exitosas.
    """
    try:
        # Detectar patrones exitosos
        if "mejor" in user_message.lower() and "cpa" in agent_response.lower():
            # El usuario preguntó por el mejor CPA y el agente respondió
            memory_manager.save_learning(
                learning_type="pattern",
                description="Usuario consulta por mejor CPA - respuesta directa funciona",
                context=f"Usuario: {user_message[:100]}\nAgente identificó correctamente el anuncio con mejor CPA",
                recommendation="Cuando pregunten por 'mejor', priorizar respuesta directa con el ganador",
                metadata={"thread_id": thread_id, "metric": "cpa"}
            )
            print("🎓 Aprendizaje automático guardado: mejor CPA")
        
        # Detectar cuando se mencionan campañas específicas
        campaigns = ["baqueira", "costa blanca", "costa luz", "tenerife"]
        mentioned_campaign = None
        for campaign in campaigns:
            if campaign in user_message.lower():
                mentioned_campaign = campaign
                break
        
        if mentioned_campaign and ("clicks" in agent_response.lower() or "conversiones" in agent_response.lower()):
            memory_manager.save_learning(
                learning_type="insight",
                description=f"Consulta exitosa sobre campaña {mentioned_campaign}",
                context=f"Usuario preguntó por {mentioned_campaign} y recibió datos de rendimiento",
                recommendation=f"Para {mentioned_campaign}, priorizar métricas de clicks y conversiones",
                metadata={"campaign": mentioned_campaign, "thread_id": thread_id}
            )
            print(f"🎓 Insight guardado sobre campaña: {mentioned_campaign}")
    
    except Exception as e:
        print(f"⚠️ Error extrayendo aprendizajes: {e}")

# Iniciar el bot
if __name__ == "__main__":
    print("🚀 Iniciando Socket Mode Handler...")
    handler = SocketModeHandler(slack_app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()
    print("✅ Bolt app is running!")