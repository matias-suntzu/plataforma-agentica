"""
Gestor de Memoria para el agente de Vivla.
Maneja memoria a corto y largo plazo usando LangGraph Checkpointer y ChromaDB.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain_core.documents import Document  # 👈 CAMBIO AQUÍ
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Gestor de memoria a largo plazo para el agente.
    
    Funcionalidades:
    - Guardar conversaciones completas
    - Guardar feedback (aprendizaje)
    - Consultar memoria histórica
    - Extraer patrones y aprendizajes
    """
    
    def __init__(
        self,
        memory_dir: str = "knowledge_base/memory",
        gemini_api_key: Optional[str] = None
    ):
        """
        Inicializa el gestor de memoria.
        
        Args:
            memory_dir: Carpeta para almacenar memoria a largo plazo
            gemini_api_key: API key de Google Gemini
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # API Key
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY no encontrada")
        
        # Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.gemini_api_key
        )
        
        # Vector stores separados para diferentes tipos de memoria
        self.conversations_store = None
        self.learnings_store = None
        
        self._init_vector_stores()
        
        logger.info(f"✅ MemoryManager inicializado en {self.memory_dir}")
    
    
    def _init_vector_stores(self):
        """Inicializa los vector stores para diferentes tipos de memoria."""
        
        # Store para conversaciones históricas
        conversations_dir = self.memory_dir / "conversations"
        conversations_dir.mkdir(exist_ok=True)
        
        try:
            self.conversations_store = Chroma(
                persist_directory=str(conversations_dir),
                embedding_function=self.embeddings,
                collection_name="conversations"
            )
            logger.info("✅ Conversations store inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando conversations store: {e}")
        
        # Store para aprendizajes (feedback, correcciones)
        learnings_dir = self.memory_dir / "learnings"
        learnings_dir.mkdir(exist_ok=True)
        
        try:
            self.learnings_store = Chroma(
                persist_directory=str(learnings_dir),
                embedding_function=self.embeddings,
                collection_name="learnings"
            )
            logger.info("✅ Learnings store inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando learnings store: {e}")
    
    
    def save_conversation(
        self,
        thread_id: str,
        user_message: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Guarda una conversación en la memoria a largo plazo.
        
        Args:
            thread_id: ID único de la conversación
            user_message: Mensaje del usuario
            agent_response: Respuesta del agente
            metadata: Metadata adicional (campañas consultadas, etc.)
        """
        if not self.conversations_store:
            logger.warning("⚠️ Conversations store no disponible")
            return
        
        try:
            # Crear documento combinado
            content = f"""
Usuario: {user_message}

Agente: {agent_response}
"""
            
            # Metadata enriquecida
            full_metadata = {
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message[:200],  # Primeros 200 chars
                "type": "conversation"
            }
            
            if metadata:
                full_metadata.update(metadata)
            
            # Crear documento
            doc = Document(
                page_content=content,
                metadata=full_metadata
            )
            
            # Guardar en vector store
            self.conversations_store.add_documents([doc])
            
            logger.info(f"💾 Conversación guardada (thread: {thread_id})")
        
        except Exception as e:
            logger.error(f"❌ Error guardando conversación: {e}")
    
    
    def save_learning(
        self,
        learning_type: str,
        description: str,
        context: str,
        recommendation: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Guarda un aprendizaje específico (feedback, corrección, patrón).
        
        Args:
            learning_type: Tipo de aprendizaje (feedback, correction, pattern, insight)
            description: Descripción breve del aprendizaje
            context: Contexto en el que ocurrió
            recommendation: Qué hacer en el futuro
            metadata: Metadata adicional
        """
        if not self.learnings_store:
            logger.warning("⚠️ Learnings store no disponible")
            return
        
        try:
            content = f"""
Tipo: {learning_type}
Descripción: {description}

Contexto:
{context}

Recomendación futura:
{recommendation}
"""
            
            full_metadata = {
                "learning_type": learning_type,
                "timestamp": datetime.now().isoformat(),
                "description": description[:200],
                "type": "learning"
            }
            
            if metadata:
                full_metadata.update(metadata)
            
            doc = Document(
                page_content=content,
                metadata=full_metadata
            )
            
            self.learnings_store.add_documents([doc])
            
            logger.info(f"🧠 Aprendizaje guardado: {learning_type}")
        
        except Exception as e:
            logger.error(f"❌ Error guardando aprendizaje: {e}")
    
    
    def get_relevant_memories(
        self,
        query: str,
        k: int = 3,
        memory_type: str = "all"
    ) -> List[Document]:
        """
        Obtiene memorias relevantes para el contexto actual.
        
        Args:
            query: Query o contexto actual
            k: Número de memorias a retornar
            memory_type: "conversations", "learnings", o "all"
            
        Returns:
            Lista de documentos relevantes
        """
        results = []
        
        try:
            # Buscar en conversaciones
            if memory_type in ["conversations", "all"] and self.conversations_store:
                conv_results = self.conversations_store.similarity_search(
                    query=query,
                    k=k
                )
                results.extend(conv_results)
            
            # Buscar en aprendizajes
            if memory_type in ["learnings", "all"] and self.learnings_store:
                learn_results = self.learnings_store.similarity_search(
                    query=query,
                    k=k
                )
                results.extend(learn_results)
            
            logger.info(f"🔍 Memorias encontradas: {len(results)} para query: '{query[:50]}...'")
            return results[:k]  # Limitar al número solicitado
        
        except Exception as e:
            logger.error(f"❌ Error buscando memorias: {e}")
            return []
    
    
    def get_memory_context(self, query: str, k: int = 3) -> str:
        """
        Obtiene contexto de memoria como string para el prompt.
        
        Args:
            query: Query actual
            k: Número de memorias a consultar
            
        Returns:
            String con el contexto de memoria
        """
        memories = self.get_relevant_memories(query, k=k)
        
        if not memories:
            return ""
        
        context_parts = ["[MEMORIA A LARGO PLAZO - EXPERIENCIAS PASADAS]"]
        
        for i, mem in enumerate(memories, 1):
            mem_type = mem.metadata.get('type', 'unknown')
            timestamp = mem.metadata.get('timestamp', 'unknown')
            content = mem.page_content.strip()
            
            context_parts.append(f"\n{i}. [{mem_type.upper()} - {timestamp[:10]}]")
            context_parts.append(content[:300] + "..." if len(content) > 300 else content)
        
        context_parts.append("\n[FIN DE MEMORIA - USA ESTOS APRENDIZAJES SI SON RELEVANTES]")
        
        return "\n".join(context_parts)
    
    
    def get_recent_conversations(self, thread_id: str, limit: int = 5) -> List[Document]:
        """
        Obtiene las conversaciones recientes de un thread específico.
        
        Args:
            thread_id: ID del thread
            limit: Número máximo de conversaciones
            
        Returns:
            Lista de conversaciones recientes
        """
        if not self.conversations_store:
            return []
        
        try:
            # Filtrar por thread_id
            results = self.conversations_store.get(
                where={"thread_id": thread_id},
                limit=limit
            )
            
            if results and results.get('documents'):
                docs = []
                for i, doc in enumerate(results['documents']):
                    docs.append(Document(
                        page_content=doc,
                        metadata=results['metadatas'][i] if results.get('metadatas') else {}
                    ))
                return docs
            
            return []
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo conversaciones recientes: {e}")
            return []
    
    
    def save_feedback(
        self,
        user_message: str,
        agent_response: str,
        feedback_type: str,
        feedback_text: str
    ):
        """
        Guarda feedback del usuario sobre una respuesta.
        
        Args:
            user_message: Mensaje original del usuario
            agent_response: Respuesta del agente
            feedback_type: "positive" o "negative"
            feedback_text: Texto del feedback
        """
        self.save_learning(
            learning_type="feedback",
            description=f"Feedback {feedback_type} del usuario",
            context=f"Usuario preguntó: {user_message}\nAgente respondió: {agent_response}",
            recommendation=feedback_text,
            metadata={"feedback_type": feedback_type}
        )
    
    
    def get_statistics(self) -> Dict[str, int]:
        """Obtiene estadísticas de la memoria."""
        stats = {
            "conversations": 0,
            "learnings": 0
        }
        
        try:
            if self.conversations_store:
                stats["conversations"] = self.conversations_store._collection.count()
            
            if self.learnings_store:
                stats["learnings"] = self.learnings_store._collection.count()
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
        
        return stats


def create_short_term_memory_summary(messages: List) -> str:
    """
    Crea un resumen de la memoria a corto plazo (conversación actual).
    
    Args:
        messages: Lista de mensajes del thread actual
        
    Returns:
        Resumen en texto
    """
    if not messages:
        return "Sin historial de conversación"
    
    summary_parts = []
    
    for msg in messages[-10:]:  # Últimos 10 mensajes
        if hasattr(msg, 'content'):
            role = "Usuario" if msg.__class__.__name__ == "HumanMessage" else "Agente"
            content = msg.content[:150]
            summary_parts.append(f"{role}: {content}")
    
    return "\n".join(summary_parts)


if __name__ == "__main__":
    """Script de prueba del MemoryManager"""
    
    print("🧪 Probando MemoryManager...")
    print("-" * 50)
    
    # Inicializar
    memory = MemoryManager()
    
    # Guardar conversación de prueba
    memory.save_conversation(
        thread_id="test_thread_001",
        user_message="Dame el TOP 3 de anuncios de Baqueira",
        agent_response="Aquí están los mejores anuncios de Baqueira con 3035, 2232 y 1026 clicks",
        metadata={"campaign": "baqueira", "period": "last_7d"}
    )
    
    # Guardar aprendizaje
    memory.save_learning(
        learning_type="pattern",
        description="Los anuncios con video de testimoniales funcionan mejor",
        context="Campaña de Baqueira mostró mejor CTR con videos testimoniales",
        recommendation="Priorizar creativos de video testimonial en futuras campañas de ski"
    )
    
    # Consultar memoria
    print("\n🔍 Consultando memoria sobre 'mejores anuncios'...")
    context = memory.get_memory_context("mejores anuncios de Baqueira", k=2)
    print(context)
    
    # Estadísticas
    print("\n📊 Estadísticas de memoria:")
    stats = memory.get_statistics()
    print(f"   Conversaciones: {stats['conversations']}")
    print(f"   Aprendizajes: {stats['learnings']}")
    
    print("\n✅ Prueba completada")