"""
Script de prueba para el sistema RAG de Vivla
"""

from rag_manager import RAGManager
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🧪 PRUEBA DEL SISTEMA RAG DE VIVLA")
    print("=" * 60)
    
    # Inicializar RAG
    print("\n1️⃣ Inicializando RAGManager...")
    rag = RAGManager()
    
    # Crear/cargar vectorstore
    print("\n2️⃣ Cargando base de conocimiento...")
    rag.create_vectorstore(force_recreate=True)  # 👈 CAMBIAR A True
    
    # Consultas de prueba
    test_queries = [
        "¿Qué significa CTR?",
        "¿Cómo se calcula el CPA?",
        "¿Qué es el ROAS?"
    ]
    
    print("\n3️⃣ Probando consultas...")
    print("-" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Consulta {i}: {query}")
        print("-" * 60)
        
        # Obtener contexto
        context = rag.get_context_for_query(query, k=2)
        
        # Mostrar resultado
        if "No se encontró información" in context:
            print("❌ No se encontró información relevante")
        else:
            print(f"✅ Contexto encontrado:")
            print(context[:600] + "..." if len(context) > 600 else context)
        
        print("-" * 60)
    
    print("\n✅ Prueba completada")
    
    # Estadísticas
    print("\n📊 ESTADÍSTICAS:")
    if rag.vectorstore:
        collection = rag.vectorstore._collection
        print(f"   Total chunks en la base: {collection.count()}")
    else:
        print("   ⚠️ Vectorstore no disponible")

if __name__ == "__main__":
    main()