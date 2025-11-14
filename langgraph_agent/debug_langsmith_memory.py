"""
Script para diagnosticar si LangSmith está guardando checkpoints
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 DIAGNÓSTICO DE MEMORIA / CHECKPOINTING")
print("=" * 70)

# 1. Verificar variables de entorno
print("\n1️⃣ Variables de entorno:")
print(f"   LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
print(f"   LANGCHAIN_API_KEY: {'✅ Configurado' if os.getenv('LANGCHAIN_API_KEY') else '❌ NO configurado'}")
print(f"   LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT', 'default')}")

# 2. Probar el agente directamente
print("\n2️⃣ Probando agente directamente (sin orchestrator):")

try:
    from langgraph_agent.core.agent import app as agent_app
    from langchain_core.messages import HumanMessage
    from langchain_core.runnables import RunnableConfig
    
    # Test 1: Primera invocación
    thread_id = "test_memory_debug_001"
    config = RunnableConfig(configurable={"thread_id": thread_id})
    
    print(f"\n📝 TURNO 1 (thread: {thread_id}):")
    result1 = agent_app.invoke(
        {"messages": [HumanMessage(content="dame TOP 3 de Baqueira")]},
        config=config
    )
    
    print(f"   Mensajes en estado: {len(result1['messages'])}")
    print(f"   Último mensaje: {result1['messages'][-1].content[:100]}...")
    
    # Test 2: Segunda invocación CON MISMO THREAD
    print(f"\n📝 TURNO 2 (MISMO thread: {thread_id}):")
    result2 = agent_app.invoke(
        {"messages": [HumanMessage(content="qué recomiendas para mejorar el cpa?")]},
        config=config  # ← Mismo thread_id
    )
    
    print(f"   Mensajes en estado: {len(result2['messages'])}")
    
    # ✅ Si la memoria funciona, debería tener MÁS mensajes (historial)
    if len(result2['messages']) > 2:
        print(f"   ✅ MEMORIA FUNCIONA: Tiene {len(result2['messages'])} mensajes (incluye historial)")
        
        # Mostrar historial
        print("\n   📜 Historial de mensajes:")
        for i, msg in enumerate(result2['messages'][-5:], 1):  # Últimos 5
            msg_type = type(msg).__name__
            content = str(msg.content)[:80] if hasattr(msg, 'content') else str(msg)[:80]
            print(f"      {i}. [{msg_type}] {content}...")
    else:
        print(f"   ❌ MEMORIA NO FUNCIONA: Solo tiene {len(result2['messages'])} mensajes")
        print(f"      (Debería tener al menos 4: msg1, resp1, msg2, resp2)")
    
    print("\n   Último mensaje:")
    final_msg = result2['messages'][-1]
    if hasattr(final_msg, 'content'):
        if isinstance(final_msg.content, str):
            print(f"   {final_msg.content[:200]}...")
        else:
            print(f"   {final_msg.content}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# 3. Verificar si el workflow tiene checkpointer
print("\n3️⃣ Verificando configuración del workflow:")

try:
    from langgraph_agent.core.agent import app as agent_app
    
    # Verificar si tiene checkpointer
    if hasattr(agent_app, 'checkpointer'):
        print(f"   ✅ Checkpointer: {type(agent_app.checkpointer).__name__}")
    else:
        print(f"   ❌ NO tiene checkpointer configurado")
    
    # Verificar el config schema
    if hasattr(agent_app, 'config_specs'):
        print(f"   Config specs: {agent_app.config_specs}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 70)