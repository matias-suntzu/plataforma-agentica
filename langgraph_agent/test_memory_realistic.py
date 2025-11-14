"""
Test realista de memoria conversacional
Simula el flujo: consulta inicial → pregunta de seguimiento
"""

from langgraph_agent.core.agent import app
from langchain_core.messages import HumanMessage

def print_response(result, turn_num):
    """Imprime la respuesta del agente de forma legible"""
    print(f"\n{'='*70}")
    print(f"🔵 TURNO {turn_num}")
    print(f"{'='*70}")
    
    last_msg = result['messages'][-1]
    
    # Verificar si tiene tool_calls
    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
        print(f"🛠️  Herramientas llamadas: {len(last_msg.tool_calls)}")
        for tc in last_msg.tool_calls:
            tool_name = tc['name'] if isinstance(tc, dict) else tc.name
            print(f"   - {tool_name}")
    
    # Mostrar contenido
    content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
    
    if isinstance(content, str) and len(content) > 0:
        print(f"\n💬 Respuesta del agente:")
        print(f"   {content[:300]}{'...' if len(content) > 300 else ''}")
    
    print(f"\n📊 Total de mensajes en historial: {len(result['messages'])}")


# ============================================
# TEST COMPLETO DE FLUJO CONVERSACIONAL
# ============================================

print("\n" + "🧪 TEST DE MEMORIA CONVERSACIONAL".center(70, "="))
print("Simulando conversación real con seguimiento de contexto\n")

thread_id = "test_realistic_001"
config = {"configurable": {"thread_id": thread_id}}

# ============================================
# TURNO 1: Consulta inicial sobre Baqueira
# ============================================
query1 = "Dame el TOP 3 de anuncios de Baqueira del último mes"
print(f"👤 Usuario: {query1}")

result1 = app.invoke(
    {"messages": [HumanMessage(content=query1)]},
    config=config
)

print_response(result1, 1)

# ============================================
# TURNO 2: Pregunta de seguimiento (usa memoria)
# ============================================
query2 = "¿Qué recomiendas para mejorar el CPA?"
print(f"\n\n👤 Usuario: {query2}")
print("🔍 Contexto esperado: El agente debe recordar que hablamos de Baqueira")

result2 = app.invoke(
    {"messages": [HumanMessage(content=query2)]},
    config=config
)

print_response(result2, 2)

# Verificar si usó el contexto
last_response = str(result2['messages'][-1].content).lower()
if 'baqueira' in last_response or '120232362248210126' in last_response:
    print("\n✅ ÉXITO: El agente RECORDÓ el contexto de Baqueira")
else:
    print("\n⚠️  ADVERTENCIA: El agente NO mencionó Baqueira explícitamente")
    print("   (Pero puede haber entendido el contexto implícitamente)")

# ============================================
# TURNO 3: Otra pregunta de seguimiento
# ============================================
query3 = "¿Cuál es la estrategia de puja de esa campaña?"
print(f"\n\n👤 Usuario: {query3}")
print("🔍 Contexto esperado: El agente debe saber que 'esa campaña' = Baqueira")

result3 = app.invoke(
    {"messages": [HumanMessage(content=query3)]},
    config=config
)

print_response(result3, 3)

# ============================================
# TURNO 4: Nuevo thread (NO debe recordar)
# ============================================
print("\n\n" + "🆕 NUEVO THREAD (sin historial)".center(70, "="))

new_thread_id = "test_realistic_002"
new_config = {"configurable": {"thread_id": new_thread_id}}

query4 = "¿De qué campaña estábamos hablando?"
print(f"👤 Usuario: {query4}")

result4 = app.invoke(
    {"messages": [HumanMessage(content=query4)]},
    config=new_config
)

print_response(result4, 4)

last_response_new = str(result4['messages'][-1].content).lower()
if 'no tengo' in last_response_new or 'no recuerdo' in last_response_new or 'no hemos' in last_response_new:
    print("\n✅ CORRECTO: El nuevo thread NO tiene acceso al historial anterior")
else:
    print("\n⚠️  El agente respondió pero debería indicar que no tiene contexto previo")

# ============================================
# RESUMEN FINAL
# ============================================
print("\n\n" + "📊 RESUMEN DEL TEST".center(70, "="))
print(f"✅ Thread 1 ({thread_id}):")
print(f"   - Total de turnos: 3")
print(f"   - Mensajes finales: {len(result3['messages'])}")
print(f"   - Memoria funcional: {'✅' if len(result3['messages']) >= 6 else '❌'}")

print(f"\n✅ Thread 2 ({new_thread_id}):")
print(f"   - Total de turnos: 1")
print(f"   - Mensajes finales: {len(result4['messages'])}")
print(f"   - Aislamiento correcto: {'✅' if len(result4['messages']) == 2 else '❌'}")

print("\n" + "="*70)
print("🎉 TEST COMPLETADO")
print("="*70)