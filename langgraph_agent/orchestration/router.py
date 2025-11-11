"""
Router V3 - FASE 2
Router mejorado con 6 categorías (agregadas: autonomous_optimization, period_comparison)

CAMBIOS vs V2:
- Ahora reconoce queries de optimización autónoma
- Detecta comparaciones de períodos
- ✅ Detecta métricas: gasto, CPA, CTR, clicks, conversiones, impresiones
- Total: 6 categorías
"""

from typing import Literal, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
import os
from datetime import datetime
import json


class RouteQueryV3(BaseModel):
    """Clasificación avanzada de consultas (6 categorías - FASE 2)."""
    
    category: Literal[
        "simple",
        "sequential",
        "agentic",
        "conversation",
        "autonomous_optimization",  # 🆕 FASE 2
        "period_comparison"         # 🆕 FASE 2
    ] = Field(description="Categoría de la consulta")
    
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
        description="Intención: 'report', 'alert', 'analysis', 'list', 'optimize', 'compare'"
    )
    requires_tools: Optional[list[str]] = Field(
        default=None,
        description="Herramientas que probablemente necesitará"
    )


# Prompt mejorado del Router V3
ROUTER_V3_PROMPT = """Eres un clasificador experto de consultas para un sistema de Meta Ads.

Clasifica la consulta en UNA de estas 6 categorías:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **SIMPLE** (Fast Path - Sin agente):
   Características:
   - Listados básicos SIN análisis NI métricas
   - Consultas de estado/existencia
   - No requiere razonamiento ni múltiples pasos
   - Respuesta directa desde herramienta
   - ❌ NO menciona: gasto, spend, CPA, CTR, conversiones, clicks, impresiones, resultados, rendimiento
   
   Ejemplos:
   ✓ "lista todas las campañas"
   ✓ "¿cuántas campañas activas tengo?"
   ✓ "muéstrame las campañas"
   ✗ "gasto de las campañas" → AGENTIC (métrica)
   ✗ "rendimiento de campañas" → AGENTIC (métrica)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 **SEQUENTIAL** (Workflow secuencial - Multi-paso):
   Características:
   - Múltiples acciones en orden específico
   - Palabras clave: "y luego", "después", "genera Y envía"
   - Flujos: Analizar → Reportar → Enviar/Alertar
   - Orquestación con pasos predefinidos
   
   Ejemplos:
   ✓ "genera un reporte de Baqueira y envíalo a Slack"
   ✓ "analiza las campañas activas y crea un resumen"
   ✓ "obtén métricas y genera slides"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 **AGENTIC** (Análisis complejo - Razonamiento):
   Características:
   - Análisis profundo con métricas
   - Comparaciones, rankings (TOP N)
   - Requiere razonamiento del LLM
   - Búsqueda + análisis combinado
   - ✅ CUALQUIER mención de métricas: gasto, spend, CPA, CTR, clicks, conversiones, impresiones, resultados, rendimiento
   - ✅ Referencias temporales: "última semana", "mes pasado", "hoy", "ayer", "durante"
   
   Ejemplos:
   ✓ "dame el TOP 3 de anuncios de Baqueira"
   ✓ "¿qué campaña tiene mejor CPA?"
   ✓ "analiza el rendimiento de las campañas de verano"
   ✓ "cuál ha sido el gasto de las campañas durante la semana pasada"
   ✓ "conversiones de Ibiza en octubre"
   ✓ "rendimiento de las campañas activas"
   ✓ "cuánto he gastado este mes"
   ✓ "resultados de las campañas"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
   ✓ "¿cuánto gasta?" (sin especificar qué)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **AUTONOMOUS_OPTIMIZATION** (🆕 FASE 2 - Optimización proactiva):
   Características:
   - Solicitud de optimización AUTOMÁTICA
   - Palabras clave: "optimiza automáticamente", "mejora automática", "optimización autónoma"
   - El usuario pide que el sistema tome decisiones y ejecute acciones
   - Workflow: Recomendación → Decisión → Ejecución → Reporte
   
   Ejemplos:
   ✓ "optimiza automáticamente mis campañas"
   ✓ "mejora automática de presupuestos"
   ✓ "ejecuta optimizaciones recomendadas"
   ✓ "aplica mejoras de forma autónoma"
   
   🚨 IMPORTANTE: Solo si menciona "automáticamente" o "autónoma"
      Si solo pide "dame recomendaciones" → AGENTIC
      Si pide "optimiza X" sin "automáticamente" → AGENTIC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **PERIOD_COMPARISON** (🆕 FASE 2 - Comparación temporal):
   Características:
   - Compara métricas entre DOS períodos de tiempo
   - Palabras clave: "compara", "vs", "versus", "diferencia entre"
   - Referencias temporales: "esta semana vs la anterior", "mes pasado vs actual"
   - Workflow: Obtener P1 → Obtener P2 → Calcular deltas → Analizar con LLM
   
   Ejemplos:
   ✓ "compara esta semana con la anterior"
   ✓ "diferencia entre este mes y el mes pasado"
   ✓ "métricas de julio vs agosto"
   ✓ "rendimiento Q1 vs Q2"
   ✓ "cómo fue la semana pasada vs esta"
   
   🚨 IMPORTANTE: Debe mencionar DOS períodos explícita o implícitamente
      "compara esta semana" (con qué?) → Si no especifica → AGENTIC
      "compara esta semana con la anterior" → PERIOD_COMPARISON

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 REGLAS CRÍTICAS:

1. **Prioridad de categorías (EN ESTE ORDEN):**
   1. Si menciona "optimiza automáticamente" → AUTONOMOUS_OPTIMIZATION
   2. Si compara 2 períodos explícitamente → PERIOD_COMPARISON
   3. Si menciona CUALQUIER métrica (gasto, CPA, CTR, clicks, conversiones, impresiones, rendimiento, resultados) → AGENTIC
   4. Si tiene múltiples pasos (Y, luego) → SEQUENTIAL
   5. Si es referencia implícita → CONVERSATION
   6. Si solo lista SIN métricas → SIMPLE

2. **Palabras clave AGENTIC (CRÍTICO):**
   - Métricas: "gasto", "spend", "CPA", "CTR", "clicks", "conversiones", "impresiones", "resultados", "rendimiento"
   - Análisis: "TOP", "mejor", "peor", "compara" (sin segundo período), "analiza"
   - Temporales: "última semana", "mes pasado", "durante", "este mes", "hoy", "ayer"
   
   ⚠️ Si la query menciona CUALQUIERA de estas palabras → AGENTIC (NO SIMPLE)

3. **Detected Intent:**
   - 'report' → genera reportes/slides
   - 'alert' → envía notificaciones/slack
   - 'analysis' → análisis de métricas
   - 'list' → solo listar datos
   - 'optimize' → 🆕 optimización proactiva
   - 'compare' → 🆕 comparación temporal

4. **Herramientas probables:**
   - Lista las herramientas que se necesitarán
   - AGENTIC con métricas: ["GetAllCampaignsMetrics"]
   - AUTONOMOUS_OPTIMIZATION: ["GetCampaignRecommendations", "UpdateAdsetBudget"]
   - PERIOD_COMPARISON: ["GetAllCampaignsMetrics"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Consulta del usuario: {query}

Clasifica la consulta y proporciona:
1. category (una de las 6)
2. confidence (0.0-1.0)
3. reasoning (explicación breve)
4. detected_intent (opcional)
5. requires_tools (opcional, lista de herramientas)
"""


class QueryRouterV3:
    """Router mejorado con 6 categorías (FASE 2) y logging estructurado."""
    
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
        
        self.structured_llm = self.llm.with_structured_output(RouteQueryV3)
        self.prompt = ChatPromptTemplate.from_template(ROUTER_V3_PROMPT)
        self.chain = self.prompt | self.structured_llm
        
        self.log_to_file = log_to_file
        self.log_file = "router_v3_decisions.jsonl"
    
    def classify(self, query: str, context: Optional[dict] = None) -> RouteQueryV3:
        """
        Clasifica una consulta con 6 categorías (V3).
        
        Args:
            query: La consulta del usuario
            context: Contexto adicional (opcional)
            
        Returns:
            RouteQueryV3 con category, confidence, reasoning, etc.
        """
        result = self.chain.invoke({"query": query})
        
        # Logging visual
        self._print_decision(query, result)
        
        # Logging estructurado a archivo
        if self.log_to_file:
            self._log_to_file(query, result, context)
        
        return result
    
    def _print_decision(self, query: str, result: RouteQueryV3):
        """Imprime la decisión del router con formato visual."""
        
        # Emojis por categoría
        category_emoji = {
            "simple": "⚡",
            "sequential": "🔗",
            "agentic": "🤖",
            "conversation": "💬",
            "autonomous_optimization": "🎯",  # 🆕
            "period_comparison": "📊"  # 🆕
        }
        
        emoji = category_emoji.get(result.category, "❓")
        
        print(f"\n{'='*60}")
        print(f"🔀 ROUTER V3 DECISION")
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
    
    def _log_to_file(self, query: str, result: RouteQueryV3, context: Optional[dict]):
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
            print(f"⚠️ Error al guardar log: {e}")


# Backward compatibility con V2
QueryRouterV2 = QueryRouterV3
RouteQueryV2 = RouteQueryV3


# Función helper para compatibilidad con V1
def route_query(query: str) -> str:
    """
    Función helper que retorna la categoría como string.
    Compatible con código que usa router V1.
    """
    router = QueryRouterV3()
    result = router.classify(query)
    return result.category


# Tests de validación
if __name__ == "__main__":
    print("\n🧪 Testing Router V3 (6 categorías)...\n")
    print("="*70)
    
    router = QueryRouterV3()
    
    test_queries = [
        # SIMPLE (sin métricas)
        ("SIMPLE", "lista todas las campañas"),
        ("SIMPLE", "¿cuántas campañas activas tengo?"),
        
        # AGENTIC (con métricas)
        ("AGENTIC", "dame el TOP 3 de anuncios de Baqueira"),
        ("AGENTIC", "¿qué campaña tiene mejor CPA?"),
        ("AGENTIC", "cuál ha sido el gasto de las campañas durante la semana pasada"),
        ("AGENTIC", "rendimiento de las campañas activas"),
        ("AGENTIC", "conversiones de Ibiza este mes"),
        
        # SEQUENTIAL
        ("SEQUENTIAL", "genera un reporte de Baqueira y envíalo a Slack"),
        ("SEQUENTIAL", "analiza las campañas activas y crea un resumen en Slides"),
        
        # CONVERSATION
        ("CONVERSATION", "¿cuál tiene mejor CPA?"),
        ("CONVERSATION", "¿y el segundo?"),
        
        # 🆕 AUTONOMOUS_OPTIMIZATION
        ("AUTONOMOUS_OPTIMIZATION", "optimiza automáticamente mis campañas"),
        ("AUTONOMOUS_OPTIMIZATION", "mejora automática de presupuestos"),
        ("AUTONOMOUS_OPTIMIZATION", "ejecuta optimizaciones recomendadas"),
        
        # 🆕 PERIOD_COMPARISON
        ("PERIOD_COMPARISON", "compara esta semana con la anterior"),
        ("PERIOD_COMPARISON", "diferencia entre este mes y el mes pasado"),
        ("PERIOD_COMPARISON", "rendimiento de julio vs agosto"),
    ]
    
    correct = 0
    total = len(test_queries)
    
    print("\n📋 RESULTADOS:\n")
    
    for expected, query in test_queries:
        result = router.classify(query)
        is_correct = result.category.upper() == expected
        
        status = "✅" if is_correct else "❌"
        print(f"{status} Query: '{query[:60]}...'")
        print(f"   Expected: {expected}, Got: {result.category.upper()}")
        
        if is_correct:
            correct += 1
        else:
            print(f"   ⚠️ Reasoning: {result.reasoning}")
        
        print()
    
    print("="*70)
    print(f"📊 Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    print("="*70)
    
    if correct == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
    else:
        print(f"\n⚠️ {total - correct} tests fallaron. Revisar el prompt del router.")