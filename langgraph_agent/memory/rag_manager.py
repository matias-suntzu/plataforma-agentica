"""
Gestor de RAG (Retrieval-Augmented Generation) para el agente de Vivla.
Maneja la carga, indexación y consulta de documentos de conocimiento.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# LangChain imports
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader,
    UnstructuredWordDocumentLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 👈 CAMBIO AQUÍ
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGManager:
    """
    Gestor de la base de conocimiento usando RAG.
    
    Funcionalidades:
    - Cargar documentos desde PDFs, TXT, DOCX
    - Crear embeddings con Google Gemini
    - Almacenar en ChromaDB
    - Buscar documentos relevantes por similitud
    """
    
    def __init__(
        self,
        knowledge_base_dir: str = "knowledge_base/documentos",
        vectorstore_dir: str = "knowledge_base/vectorstore",
        gemini_api_key: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Inicializa el gestor de RAG.
        
        Args:
            knowledge_base_dir: Carpeta con documentos fuente
            vectorstore_dir: Carpeta para la base de datos vectorial
            gemini_api_key: API key de Google Gemini
            chunk_size: Tamaño de los chunks de texto
            chunk_overlap: Overlap entre chunks
        """
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.vectorstore_dir = Path(vectorstore_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # API Key de Gemini
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en variables de entorno")
        
        # Crear carpetas si no existen
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        self.vectorstore_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.gemini_api_key
        )
        
        # Text splitter para chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Vector store
        self.vectorstore = None
        
        logger.info(f"✅ RAGManager inicializado")
        logger.info(f"📁 Documentos: {self.knowledge_base_dir}")
        logger.info(f"🗄️ Vectorstore: {self.vectorstore_dir}")
    
    
    def load_documents(self) -> List[Document]:
        """
        Carga todos los documentos desde la carpeta de conocimiento.
        
        Soporta: PDF, TXT, DOCX
        
        Returns:
            Lista de documentos de LangChain
        """
        documents = []
        
        if not self.knowledge_base_dir.exists():
            logger.warning(f"⚠️ Carpeta {self.knowledge_base_dir} no existe")
            return documents
        
        # Cargar PDFs
        pdf_files = list(self.knowledge_base_dir.glob("*.pdf"))
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"✅ PDF cargado: {pdf_file.name} ({len(docs)} páginas)")
            except Exception as e:
                logger.error(f"❌ Error cargando {pdf_file.name}: {e}")
        
        # Cargar TXT
        txt_files = list(self.knowledge_base_dir.glob("*.txt"))
        for txt_file in txt_files:
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"✅ TXT cargado: {txt_file.name}")
            except Exception as e:
                logger.error(f"❌ Error cargando {txt_file.name}: {e}")
        
        # Cargar DOCX
        docx_files = list(self.knowledge_base_dir.glob("*.docx"))
        for docx_file in docx_files:
            try:
                loader = UnstructuredWordDocumentLoader(str(docx_file))
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"✅ DOCX cargado: {docx_file.name}")
            except Exception as e:
                logger.error(f"❌ Error cargando {docx_file.name}: {e}")
        
        logger.info(f"📚 Total documentos cargados: {len(documents)}")
        return documents
    
    
    def create_vectorstore(self, force_recreate: bool = False) -> Chroma:
        """
        Crea o carga la base de datos vectorial.
        
        Args:
            force_recreate: Si True, borra y recrea el vectorstore
            
        Returns:
            Instancia de ChromaDB
        """
        # Si ya existe y no forzamos recrear, cargar existente
        if self.vectorstore_dir.exists() and not force_recreate:
            try:
                self.vectorstore = Chroma(
                    persist_directory=str(self.vectorstore_dir),
                    embedding_function=self.embeddings
                )
                logger.info(f"✅ Vectorstore cargado desde {self.vectorstore_dir}")
                return self.vectorstore
            except Exception as e:
                logger.warning(f"⚠️ Error cargando vectorstore existente: {e}")
                logger.info("Recreando vectorstore...")
        
        # Cargar documentos
        documents = self.load_documents()
        
        if not documents:
            logger.warning("⚠️ No hay documentos para indexar")
            return None
        
        # Hacer chunking
        logger.info("✂️ Dividiendo documentos en chunks...")
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"📦 Total chunks creados: {len(chunks)}")
        
        # Crear vectorstore
        logger.info("🔄 Creando embeddings y vectorstore (esto puede tardar)...")
        
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(self.vectorstore_dir)
        )
        
        logger.info(f"✅ Vectorstore creado exitosamente en {self.vectorstore_dir}")
        return self.vectorstore
    
    
    def query(
        self,
        query: str,
        k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Busca documentos relevantes en la base de conocimiento.
        
        Args:
            query: Pregunta o consulta
            k: Número de documentos a retornar
            filter_metadata: Filtros opcionales por metadata
            
        Returns:
            Lista de documentos más relevantes
        """
        if not self.vectorstore:
            logger.warning("⚠️ Vectorstore no inicializado. Llamando create_vectorstore()...")
            self.create_vectorstore()
        
        if not self.vectorstore:
            logger.error("❌ No hay vectorstore disponible")
            return []
        
        try:
            # Búsqueda por similitud
            results = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter_metadata
            )
            
            logger.info(f"🔍 Query: '{query[:50]}...' - Resultados: {len(results)}")
            return results
        
        except Exception as e:
            logger.error(f"❌ Error en búsqueda: {e}")
            return []
    
    
    def get_context_for_query(self, query: str, k: int = 3) -> str:
        """
        Obtiene contexto relevante como string para agregar al prompt.
        
        Args:
            query: Pregunta del usuario
            k: Número de documentos a consultar
            
        Returns:
            String con el contexto combinado
        """
        docs = self.query(query, k=k)
        
        if not docs:
            return "No se encontró información relevante en la base de conocimiento."
        
        # Combinar contenido de documentos
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Desconocido')
            content = doc.page_content.strip()
            context_parts.append(f"[Fuente {i}: {Path(source).name}]\n{content}")
        
        context = "\n\n---\n\n".join(context_parts)
        return context
    
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Agrega nuevos documentos al vectorstore existente.
        
        Args:
            documents: Lista de documentos a agregar
        """
        if not self.vectorstore:
            logger.warning("⚠️ Vectorstore no existe. Creándolo primero...")
            self.create_vectorstore()
        
        if not documents:
            logger.warning("⚠️ No hay documentos para agregar")
            return
        
        # Hacer chunking
        chunks = self.text_splitter.split_documents(documents)
        
        # Agregar al vectorstore
        self.vectorstore.add_documents(chunks)
        logger.info(f"✅ {len(chunks)} chunks agregados al vectorstore")
    
    
    def delete_vectorstore(self) -> None:
        """Elimina completamente el vectorstore."""
        import shutil
        
        if self.vectorstore_dir.exists():
            shutil.rmtree(self.vectorstore_dir)
            logger.info(f"🗑️ Vectorstore eliminado: {self.vectorstore_dir}")
        
        self.vectorstore = None


# Función helper para uso rápido
def quick_query(query: str, k: int = 3) -> str:
    """
    Función rápida para consultar la base de conocimiento.
    
    Args:
        query: Pregunta del usuario
        k: Número de documentos a retornar
        
    Returns:
        Contexto relevante como string
    """
    rag = RAGManager()
    rag.create_vectorstore()  # Carga si existe, crea si no
    return rag.get_context_for_query(query, k=k)


if __name__ == "__main__":
    """Script de prueba del RAGManager"""
    
    print("🧪 Probando RAGManager...")
    print("-" * 50)
    
    # Inicializar
    rag = RAGManager()
    
    # Crear/cargar vectorstore
    rag.create_vectorstore()
    
    # Hacer consultas de prueba
    test_queries = [
        "¿Qué es Vivla?",
        "¿Qué destinos ofrece Vivla?",
        "¿Cómo funciona la copropiedad?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        context = rag.get_context_for_query(query, k=2)
        print(f"📚 Contexto encontrado:\n{context[:300]}...\n")
        print("-" * 50)