"""
Script para probar memoria conversacional
Ejecutar: python test_memory.py
"""

import requests
import json

# URL de tu API
API_URL = "https://plataforma-agentica.onrender.com"  # Cambiar por tu URL
# O para local: API_URL = "http://localhost:8000"

def test_memory():
    """
    Prueba que el agente recuerde el contexto de conversaciones previas.
    """
    print("🧪 TEST DE MEMORIA CONVERSACIONAL")
    print("=" * 70)
    
    # ============================================
    # TURNO 1: Primera pregunta
    # ============================================
    print("\n📝 TURNO 1: Preguntando por Baqueira...")
    
    response1 = requests.post(
        f"{API_URL}/query",
        json={
            "query": "dame TOP 3 de Baqueira del último mes",
            "user_id": "test_memory"
            # No enviamos thread_id, se generará uno nuevo
        }
    )
    
    print(f"Status: {response1.status_code}")
    
    if response1.status_code != 200:
        print(f"❌ ERROR: {response1.text}")
        return False
    
    data1 = response1.json()
    
    # ✅ Verificar estructura de respuesta
    print("\nKeys en respuesta:", list(data1.keys()))
    
    thread_id = data1.get("thread_id")
    response_text = data1.get("response")
    
    if not thread_id:
        print("❌ ERROR: No se recibió thread_id")
        print("Respuesta completa:", data1)
        return False
    
    if not response_text:
        print("❌ ERROR: No se recibió response")
        print("Respuesta completa:", data1)
        return False
    
    print(f"✅ Respuesta recibida")
    print(f"🔑 Thread ID: {thread_id}")
    print(f"📊 Workflow: {data1.get('workflow_type')}")
    print(f"💬 Respuesta: {response_text[:200]}...")
    
    # ============================================
    # TURNO 2: Pregunta de seguimiento
    # ============================================
    print("\n" + "=" * 70)
    print("📝 TURNO 2: Pregunta de seguimiento (debe recordar Baqueira)...")
    
    response2 = requests.post(
        f"{API_URL}/query",
        json={
            "query": "y qué recomiendas hacer para mejorar el cpa?",
            "thread_id": thread_id,  # ← Enviar el mismo thread_id
            "user_id": "test_memory"
        }
    )
    
    print(f"Status: {response2.status_code}")
    
    if response2.status_code != 200:
        print(f"❌ ERROR: {response2.text}")
        return False
    
    data2 = response2.json()
    
    print(f"✅ Respuesta recibida")
    print(f"🔑 Thread ID: {data2.get('thread_id')}")
    print(f"📊 Workflow: {data2.get('workflow_type')}")
    print(f"💬 Respuesta: {data2.get('response', '')[:300]}...")
    
    # ============================================
    # VERIFICACIÓN
    # ============================================
    print("\n" + "=" * 70)
    print("🔍 VERIFICACIÓN:")
    
    # Verificar que se mantuvo el thread_id
    if data2.get("thread_id") != thread_id:
        print("❌ ERROR: Thread ID cambió entre turnos")
        return False
    else:
        print("✅ Thread ID se mantuvo correctamente")
    
    # Verificar que NO preguntó de nuevo por la campaña
    response_text = data2.get("response", "").lower()
    
    if "buscar" in response_text or "qué campaña" in response_text:
        print("❌ ERROR: El agente NO recordó la campaña de Baqueira")
        print("   Respuesta:", response_text[:200])
        return False
    elif "baqueira" in response_text or "recomend" in response_text:
        print("✅ El agente SÍ recordó el contexto (habla de Baqueira o recomendaciones)")
        return True
    else:
        print("⚠️ No se puede confirmar si recordó o no")
        print("   Respuesta:", response_text[:200])
        return None
    
    # ============================================
    # TURNO 3: Otra pregunta de seguimiento
    # ============================================
    print("\n" + "=" * 70)
    print("📝 TURNO 3: Tercera pregunta de seguimiento...")
    
    response3 = requests.post(
        f"{API_URL}/query",
        json={
            "query": "cuál es el anuncio con mejor ctr?",
            "thread_id": thread_id,  # ← Mismo thread_id
            "user_id": "test_memory"
        }
    )
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"✅ Respuesta recibida")
        print(f"💬 Respuesta: {data3.get('response', '')[:300]}...")
    else:
        print(f"❌ ERROR: {response3.text}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETADO")
    print("=" * 70)
    
    return True


def test_new_conversation():
    """
    Prueba que se puede iniciar una nueva conversación.
    """
    print("\n\n🧪 TEST DE NUEVA CONVERSACIÓN")
    print("=" * 70)
    
    # Resetear conversación
    response = requests.post(f"{API_URL}/reset")
    data = response.json()
    
    new_thread_id = data.get("thread_id")
    print(f"✅ Nueva conversación iniciada")
    print(f"🔑 Nuevo Thread ID: {new_thread_id}")
    
    # Primera pregunta de la nueva conversación
    response2 = requests.post(
        f"{API_URL}/query",
        json={
            "query": "lista todas las campañas",
            "thread_id": new_thread_id,
            "user_id": "test_memory"
        }
    )
    
    data2 = response2.json()
    print(f"✅ Respuesta: {data2.get('response')[:200]}...")
    
    return True


if __name__ == "__main__":
    try:
        # Test 1: Memoria conversacional
        success = test_memory()
        
        if success:
            print("\n🎉 MEMORIA CONVERSACIONAL FUNCIONA CORRECTAMENTE")
        else:
            print("\n❌ PROBLEMA CON LA MEMORIA CONVERSACIONAL")
        
        # Test 2: Nueva conversación
        test_new_conversation()
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()