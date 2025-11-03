"""
Router V2 - Día 2
Router mejorado con 4 categorías:
- simple: Listados básicos
- sequential: Flujos multi-paso (ej: Analizar → Reportar → Enviar)
- agentic: Análisis complejos con razonamiento
- conversation: Preguntas de seguimiento

MEJORAS vs V1:
- Detecta intención de reportes/automatización
- Identifica flujos secuenciales
- Logging estructurado para debugging
"""

from typing import Literal, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
import os
from datetime import datetime
import json


class RouteQueryV2(BaseModel):
    """Clasificación avanzada de consultas (4 categorías)."""
    
    category: Literal["simple", "sequential", "agentic", "conversation"] = Field(
        description="Categoría de la consulta"
    )
    confidence: float = Field(
        description="Nivel de confianza (0.0 a 1.0)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Explicación de la clasificación"
    )
    detected_intent: Optional[str] = Field(
        default=None,
        description="Intención detectada: 'report', 'alert', 'analysis', 'list'"
    )
    requires_tools: Optional[list[str]] = Field(
        default=None,
        description="Herramientas que probablemente necesitará"
    )


# Prompt mejorado del Router
ROUTER_V2_PROMPT = """Eres un clasificador experto de consultas para un sistema de Meta Ads.

Clasifica la consulta en UNA de estas 4 categorías:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **SIMPLE** (Fast Path - Sin agente):
   Características:
   - Listados básicos sin análisis
   - Consultas de estado/existencia
   - No requiere razonamiento ni múltiples pasos
   - Respuesta directa desde herramienta
   
   Ejemplos:
   ✓ "lista todas las campañas"
   ✓ "¿cuántas campañas activas tengo?"
   ✓ "muéstrame las campañas"
   ✓ "estado de la cuenta"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 **SEQUENTIAL** (Workflow secuencial - Multi-paso):
   Características:
   - Múltiples acciones en orden específico
   - Palabras clave: "y luego", "después", "genera Y envía"
   - Flujos tipo: Analizar → Reportar → Enviar/Alertar
   - Requiere orquestación pero pasos predefinidos
   
   Ejemplos:
   ✓ "genera un reporte de Baqueira y envíalo a Slack"
   ✓ "analiza las campañas activas y crea un resumen"
   ✓ "obtén métricas de esta semana y genera slides"
   ✓ "compara períodos y envía alerta si hay anomalías"
   
   Detectar patrones:
   - "genera [algo] y envía/manda a [destino]"
   - "analiza [algo] y luego [acción]"
   - "crea [X], después [Y]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 **AGENTIC** (Análisis complejo - Razonamiento):
   Características:
   - Análisis profundo con métricas
   - Comparaciones, rankings (TOP N)
   - Requiere razonamiento del LLM
   - Búsqueda + análisis combinado
   - Cualquier mención de métricas (CPA, CTR, clicks, etc.)
   
   Ejemplos:
   ✓ "dame el TOP 3 de anuncios de Baqueira"
   ✓ "¿qué campaña tiene mejor CPA?"
   ✓ "compara este mes vs el mes pasado"
   ✓ "analiza el rendimiento de las campañas de verano"
   ✓ "busca anomalías en el gasto"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 **CONVERSATION** (Pregunta de seguimiento):
   Características:
   - Referencias implícitas ("ese", "la segunda", "el mejor")
   - Pronombres sin contexto explícito
   - Requiere memoria de mensajes anteriores
   - Preguntas cortas sin entidad clara
   
   Ejemplos:
   ✓ "¿cuál tiene mejor CPA?" (después de ver lista)
   ✓ "¿y el segundo?"
   ✓ "dime más sobre esa campaña"
   ✓ "¿cuánto gasta?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 REGLAS CRÍTICAS:

1. **Prioridad de categorías:**
   - Si tiene múltiples pasos explícitos (Y, luego) → SEQUENTIAL
   - Si menciona métricas/análisis → AGENTIC
   - Si es referencia implícita → CONVERSATION
   - Si solo lista → SIMPLE

2. **Manejo de ambigüedad:**
   - "genera reporte" solo → AGENTIC
   - "genera reporte Y envía" → SEQUENTIAL
   - Si hay duda entre SIMPLE y otro → elegir el otro

3. **Detected Intent:**
   - 'report' → genera reportes/slides
   - 'alert' → envía notificaciones/slack
   - 'analysis' → análisis de métricas
   - 'list' → solo listar datos

4. **Herramientas probables:**
   - Lista las herramientas que se necesitarán
   - Ejemplo: ["BuscarIdCampanaInput", "ObtenerAnunciosPorRendimientoInput"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Consulta del usuario: {query}

Clasifica la consulta y proporciona:
1. category (simple/sequential/agentic/conversation)
2. confidence (0.0-1.0)
3. reasoning (explicación breve)
4. detected_intent (opcional)
5. requires_tools (opcional, lista de herramientas)
"""


class QueryRouterV2:
    """Router mejorado con 4 categorías y logging estructurado."""
    
    def __init__(
        self, 
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.0,
        log_to_file: bool = True
    ):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        self.structured_llm = self.llm.with_structured_output(RouteQueryV2)
        self.prompt = ChatPromptTemplate.from_template(ROUTER_V2_PROMPT)
        self.chain = self.prompt | self.structured_llm
        
        self.log_to_file = log_to_file
        self.log_file = "router_v2_decisions.jsonl"
    
    def classify(self, query: str, context: Optional[dict] = None) -> RouteQueryV2:
        """
        Clasifica una consulta con categorización mejorada.
        
        Args:
            query: La consulta del usuario
            context: Contexto adicional (opcional, para futuro)
            
        Returns:
            RouteQueryV2 con category, confidence, reasoning, etc.
        """
        result = self.chain.invoke({"query": query})
        
        # Logging visual
        self._print_decision(query, result)
        
        # Logging estructurado a archivo
        if self.log_to_file:
            self._log_to_file(query, result, context)
        
        return result
    
    def _print_decision(self, query: str, result: RouteQueryV2):
        """Imprime la decisión del router con formato visual."""
        
        # Emojis por categoría
        category_emoji = {
            "simple": "⚡",
            "sequential": "🔗",
            "agentic": "🤖",
            "conversation": "💬"
        }
        
        emoji = category_emoji.get(result.category, "❓")
        
        print(f"\n{'='*60}")
        print(f"🔀 ROUTER V2 DECISION")
        print(f"{'='*60}")
        print(f"   Query: '{query}'")
        print(f"   {emoji} Category: {result.category.upper()}")
        print(f"   📊 Confidence: {result.confidence:.2f}")
        print(f"   💡 Reasoning: {result.reasoning}")
        
        if result.detected_intent:
            print(f"   🎯 Intent: {result.detected_intent}")
        
        if result.requires_tools:
            print(f"   🔧 Tools: {', '.join(result.requires_tools)}")
        
        print(f"{'='*60}\n")
    
    def _log_to_file(self, query: str, result: RouteQueryV2, context: Optional[dict]):
        """Guarda la decisión en un archivo JSONL para análisis."""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "category": result.category,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "detected_intent": result.detected_intent,
            "requires_tools": result.requires_tools,
            "context": context
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️  Error al guardar log: {e}")


# Función helper para compatibilidad con V1
def route_query(query: str) -> str:
    """
    Función helper que retorna la categoría como string.
    Compatible con código que usa router V1.
    """
    router = QueryRouterV2()
    result = router.classify(query)
    return result.category


# Tests de validación
if __name__ == "__main__":
    print("\n🧪 Testing Router V2...\n")
    print("="*70)
    
    router = QueryRouterV2()
    
    test_queries = [
        # SIMPLE
        ("SIMPLE", "lista todas las campañas"),
        ("SIMPLE", "¿cuántas campañas activas tengo?"),
        
        # SEQUENTIAL
        ("SEQUENTIAL", "genera un reporte de Baqueira y envíalo a Slack"),
        ("SEQUENTIAL", "analiza las campañas activas y crea un resumen en Slides"),
        
        # AGENTIC
        ("AGENTIC", "dame el TOP 3 de anuncios de Baqueira"),
        ("AGENTIC", "¿qué campaña tiene mejor CPA?"),
        ("AGENTIC", "compara este mes vs el mes pasado"),
        
        # CONVERSATION
        ("CONVERSATION", "¿cuál tiene mejor CPA?"),
        ("CONVERSATION", "¿y el segundo?"),
    ]
    
    correct = 0
    total = len(test_queries)
    
    for expected, query in test_queries:
        result = router.classify(query)
        is_correct = result.category.upper() == expected
        
        status = "✅" if is_correct else "❌"
        print(f"{status} Expected: {expected}, Got: {result.category.upper()}")
        
        if is_correct:
            correct += 1
    
    print("\n" + "="*70)
    print(f"📊 Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    print("="*70)