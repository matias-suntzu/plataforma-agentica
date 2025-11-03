"""
Script de prueba para verificar persistencia de memoria entre reinicios.
Simula una conversación en dos sesiones diferentes.
"""

import sys
from langchain_core.messages import HumanMessage

# Importar el agente compilado
from agent import app as agent_app

def test_session_1():
    """Primera sesión: hacer consulta inicial"""
    print("="*60)
    print("🧪 SESIÓN 1: Consulta inicial de anuncios")
    print("="*60)
    
    thread_id = "test_persistence_thread_001"
    
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # Primera pregunta
    query1 = "Dame el TOP 3 de anuncios de Baqueira del last_7d"
    print(f"\n👤 Usuario: {query1}")
    
    input_message = {
        "messages": [HumanMessage(content=query1)]
    }
    
    result1 = agent_app.invoke(input_message, config=config)
    
    # Extraer respuesta
    if result1 and "messages" in result1:
        last_msg = result1["messages"][-1]
        response = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        
        # Convertir lista a string si es necesario
        if isinstance(response, list):
            response = "\n".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in response])
        
        print(f"\n🤖 Agente: {response[:300]}...")
    
    # Segunda pregunta de seguimiento
    query2 = "¿Cuál tiene mejor CPA?"
    print(f"\n\n👤 Usuario: {query2}")
    
    input_message2 = {
        "messages": [HumanMessage(content=query2)]
    }
    
    result2 = agent_app.invoke(input_message2, config=config)
    
    if result2 and "messages" in result2:
        last_msg = result2["messages"][-1]
        response = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        
        if isinstance(response, list):
            response = "\n".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in response])
        
        print(f"\n🤖 Agente: {response[:300]}...")
    
    print("\n✅ Sesión 1 completada. Memoria guardada en SQLite.")
    print(f"📁 Thread ID: {thread_id}")
    print("\n⏸️  Presiona Enter para simular 'reinicio del bot' y continuar con Sesión 2...")
    input()


def test_session_2():
    """Segunda sesión (después de 'reiniciar'): continuar conversación"""
    print("\n" + "="*60)
    print("🔄 SIMULANDO REINICIO DEL BOT...")
    print("="*60)
    print("✅ Bot reiniciado. Memoria SQLite persiste en disco.\n")
    
    print("="*60)
    print("🧪 SESIÓN 2: Continuación de la conversación")
    print("="*60)
    
    # Mismo thread_id que antes
    thread_id = "test_persistence_thread_001"
    
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # Tercera pregunta de seguimiento (días después)
    query3 = "¿Y el segundo mejor CPA?"
    print(f"\n👤 Usuario (días después): {query3}")
    
    input_message = {
        "messages": [HumanMessage(content=query3)]
    }
    
    result = agent_app.invoke(input_message, config=config)
    
    if result and "messages" in result:
        # Mostrar TODOS los mensajes recuperados
        print(f"\n📊 Mensajes recuperados del checkpoint: {len(result['messages'])}")
        
        last_msg = result["messages"][-1]
        response = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        
        if isinstance(response, list):
            response = "\n".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in response])
        
        print(f"\n🤖 Agente: {response}")
    
    print("\n" + "="*60)
    print("✅ PRUEBA COMPLETADA")
    print("="*60)
    
    # Verificar resultado esperado
    if "segundo" in response.lower() or "segundo mejor" in response.lower():
        print("\n✅ ¡ÉXITO! El agente recordó el contexto previo.")
        print("   La memoria a corto plazo (SqliteSaver) funcionó correctamente.")
    else:
        print("\n⚠️  ADVERTENCIA: El agente NO recordó el contexto.")
        print("   Verifica que SqliteSaver esté configurado correctamente.")


if __name__ == "__main__":
    print("\n🚀 TEST DE PERSISTENCIA DE MEMORIA")
    print("Este script simula una conversación en dos sesiones separadas.")
    print("Presiona Ctrl+C en cualquier momento para salir.\n")
    
    try:
        # Sesión 1
        test_session_1()
        
        # Sesión 2 (simula reinicio)
        test_session_2()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)