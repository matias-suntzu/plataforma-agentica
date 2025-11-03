"""
Router Clasificador - Día 1
Clasifica consultas en SIMPLE vs COMPLEJO
"""

from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
import os

# Modelo de salida estructurada
class RouteQuery(BaseModel):
    """Clasificación de la consulta del usuario."""
    
    category: Literal["simple", "complejo"] = Field(
        description="Categoría de la consulta: 'simple' para estado/listados, 'complejo' para análisis/comparaciones"
    )
    confidence: float = Field(
        description="Nivel de confianza en la clasificación (0.0 a 1.0)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Breve explicación de por qué se clasificó así"
    )


# Prompt del Router
ROUTER_PROMPT = """Eres un clasificador de consultas para un sistema de Meta Ads.

Tu tarea es clasificar la consulta del usuario en UNA de estas dos categorías:

**SIMPLE** (Fast Path - Sin usar agente):
- Listar campañas activas/todas
- Estado de cuenta
- Consultas de existencia ("¿existe la campaña X?")
- Listados generales sin análisis
- Ejemplos:
  * "lista todas las campañas"
  * "muéstrame las campañas activas"
  * "¿cuántas campañas tengo?"
  * "estado de la cuenta"

**COMPLEJO** (Agentic - Requiere análisis):
- TOP N anuncios con métricas
- Comparaciones entre períodos
- Análisis de rendimiento
- Búsqueda + Análisis combinado
- Generación de reportes
- Cualquier cosa con "mejor", "peor", "comparar", "analizar"
- Ejemplos:
  * "TOP 3 anuncios de Baqueira"
  * "compara este mes vs mes pasado"
  * "¿cuál tiene mejor CPA?"
  * "genera reporte de la campaña X"

REGLAS CRÍTICAS:
1. Si hay duda, clasifica como COMPLEJO (mejor sobre-procesar que dar respuesta incompleta)
2. Solo clasifica como SIMPLE si es LITERALMENTE un listado sin análisis
3. Cualquier mención de métricas (CPA, CTR, clicks, etc.) → COMPLEJO
4. Preguntas de seguimiento del usuario → COMPLEJO (requieren contexto)

Consulta del usuario: {query}

Clasifica y explica tu razonamiento."""


class QueryRouter:
    """Router que clasifica consultas en SIMPLE vs COMPLEJO."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp", temperature: float = 0.0):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        # Vincular el modelo con salida estructurada
        self.structured_llm = self.llm.with_structured_output(RouteQuery)
        
        # Crear el prompt template
        self.prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
        
        # Chain completo
        self.chain = self.prompt | self.structured_llm
    
    def classify(self, query: str) -> RouteQuery:
        """
        Clasifica una consulta del usuario.
        
        Args:
            query: La consulta del usuario
            
        Returns:
            RouteQuery con category, confidence y reasoning
        """
        result = self.chain.invoke({"query": query})
        
        print(f"\n🔀 ROUTER DECISION:")
        print(f"   Query: '{query}'")
        print(f"   Category: {result.category.upper()}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Reasoning: {result.reasoning}")
        print("-" * 60)
        
        return result


# Función helper para uso rápido
def route_query(query: str) -> str:
    """
    Función helper que retorna directamente la categoría como string.
    
    Args:
        query: La consulta del usuario
        
    Returns:
        "simple" o "complejo"
    """
    router = QueryRouter()
    result = router.classify(query)
    return result.category


# Tests de validación
if __name__ == "__main__":
    print("🧪 Testing Router...")
    print("=" * 60)
    
    router = QueryRouter()
    
    test_queries = [
        # SIMPLE
        "lista todas las campañas",
        "muéstrame las campañas activas",
        "¿cuántas campañas tengo?",
        
        # COMPLEJO
        "dame el TOP 3 de anuncios de Baqueira",
        "¿cuál tiene mejor CPA?",
        "compara este mes vs el anterior",
        "genera un reporte de la campaña de verano",
    ]
    
    for query in test_queries:
        result = router.classify(query)
        print()