"""
Router V4 - SIMPLIFICADO (3 categorías)
Reduce complejidad y mejora precisión
"""

import os
from typing import Literal, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field


# ========== SCHEMA ==========

class RouteQueryV4(BaseModel):
    """Clasificación simplificada de consultas (3 categorías)"""
    
    category: Literal["simple", "agentic", "multi_agent"] = Field(
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
        description="Intención: 'list', 'metrics', 'config', 'compare', 'report'"
    )


# ========== PROMPT ==========

ROUTER_V4_PROMPT = """
Eres un clasificador experto de consultas para un sistema de Meta Ads.

Clasifica la consulta en UNA de estas 3 categorías:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ **SIMPLE** (Fast Path - Sin agente):
   Características:
   - Listados básicos SIN análisis
   - Consultas directas con respuesta obvia
   - NO requiere razonamiento del LLM
   - Respuesta directa desde herramienta
   - NO menciona métricas de rendimiento NI recomendaciones
   
   Ejemplos:
   ✅ "lista todas las campañas"
   ✅ "¿cuántas campañas activas tengo?"
   ✅ "muéstrame las campañas"
   ❌ "gasto de las campañas" → AGENTIC (métrica)
   ❌ "recomienda mejoras" → AGENTIC (recomendación)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 **AGENTIC** (Con agente especializado):
   Características:
   - Requiere llamar a ConfigAgent, PerformanceAgent o RecommendationAgent
   - Necesita búsqueda de campaña por nombre
   - Métricas o configuración de UNA campaña
   - Comparaciones de períodos
   - TOP N anuncios
   - Recomendaciones específicas de UNA campaña 🆕
   
   Ejemplos:
   ✅ "¿qué presupuesto tiene Baqueira?" → ConfigAgent
   ✅ "gasto de Ibiza esta semana" → PerformanceAgent
   ✅ "TOP 3 de anuncios de Costa Blanca" → PerformanceAgent
   ✅ "compara esta semana con la anterior" → PerformanceAgent
   ✅ "estrategia de puja de Menorca" → ConfigAgent
   ✅ "dame recomendaciones para Baqueira" → RecommendationAgent 🆕
   ✅ "¿cómo mejorar el CPA de Ibiza?" → RecommendationAgent 🆕
   ✅ "¿debería activar Advantage+ en Costa Blanca?" → RecommendationAgent 🆕

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔀 **MULTI_AGENT** (Requiere varios agentes):
   Características:
   - Análisis completo (config + rendimiento + recomendaciones)
   - "¿Cómo está X?" sin especificar
   - Reportes completos con sugerencias
   - Necesita información de múltiples agentes
   
   Ejemplos:
   ✅ "analiza la campaña de Baqueira"
   ✅ "¿cómo está Costa del Sol?"
   ✅ "dame un reporte completo de Ibiza"
   ✅ "qué me puedes decir de Menorca"
   ✅ "análisis completo con recomendaciones de Baqueira" 🆕

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 REGLAS CRÍTICAS:

1. **Prioridad de clasificación:**
   1. Si solo pide listar SIN métricas NI recomendaciones → SIMPLE
   2. Si menciona una campaña específica + métricas → AGENTIC (PerformanceAgent)
   3. Si menciona una campaña específica + config → AGENTIC (ConfigAgent)
   4. Si menciona una campaña específica + recomendaciones → AGENTIC (RecommendationAgent) 🆕
   5. Si pide "análisis completo" o "cómo está" → MULTI_AGENT

2. **Palabras clave AGENTIC:**
   - Métricas: gasto, conversiones, clicks, CTR, CPM, CPC, CPA
   - Config: presupuesto, estrategia, puja, objetivo
   - Comparaciones: "compara", "vs", "versus"
   - TOP: "TOP 3", "mejores", "peores"
   - Recomendaciones: "recomienda", "optimiza", "mejora", "sugerencia", "debería", "Advantage+" 🆕

3. **Detected Intent:**
   - 'list' → solo listar (SIMPLE)
   - 'metrics' → métricas de rendimiento (AGENTIC/PerformanceAgent)
   - 'config' → configuración técnica (AGENTIC/ConfigAgent)
   - 'compare' → comparación de períodos (AGENTIC/PerformanceAgent)
   - 'recommendation' → recomendaciones (AGENTIC/RecommendationAgent) 🆕
   - 'report' → reporte completo (MULTI_AGENT)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Consulta del usuario: {query}

Clasifica la consulta y proporciona:
1. category (simple / agentic / multi_agent)
2. confidence (0.0-1.0)
3. reasoning (explicación breve)
4. detected_intent (opcional: list / metrics / config / compare / recommendation / report)
"""


# ========== ROUTER ==========

class QueryRouterV4:
    """Router simplificado con 3 categorías"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.0,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        self.structured_llm = self.llm.with_structured_output(RouteQueryV4)
        self.prompt = ChatPromptTemplate.from_template(ROUTER_V4_PROMPT)
        self.chain = self.prompt | self.structured_llm
    
    def classify(self, query: str) -> RouteQueryV4:
        """
        Clasifica una consulta en 3 categorías.
        
        Args:
            query: La consulta del usuario
            
        Returns:
            RouteQueryV4 con category, confidence, reasoning, etc.
        """
        result = self.chain.invoke({"query": query})
        
        # Log visual
        self._print_decision(query, result)
        
        return result
    
    def _print_decision(self, query: str, result: RouteQueryV4):
        """Imprime la decisión con formato visual"""
        emoji_map = {
            "simple": "⚡",
            "agentic": "🤖",
            "multi_agent": "🔀"
        }
        
        emoji = emoji_map.get(result.category, "❓")
        
        print(f"\n{'='*60}")
        print(f"🔀 ROUTER V4 DECISION")
        print(f"{'='*60}")
        print(f"   Query: '{query}'")
        print(f"   {emoji} Category: {result.category.upper()}")
        print(f"   📊 Confidence: {result.confidence:.2f}")
        print(f"   💡 Reasoning: {result.reasoning}")
        
        if result.detected_intent:
            print(f"   🎯 Intent: {result.detected_intent}")
        
        print(f"{'='*60}\n")


# ========== EXPORTAR ==========

router_v4 = QueryRouterV4()


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing Router V4 (3 categorías)...\n")
    
    test_cases = [
        # SIMPLE
        ("lista todas las campañas", "simple"),
        ("¿cuántas campañas activas tengo?", "simple"),
        
        # AGENTIC
        ("¿qué presupuesto tiene Baqueira?", "agentic"),
        ("gasto de Ibiza esta semana", "agentic"),
        ("TOP 3 de anuncios de Costa Blanca", "agentic"),
        ("compara esta semana con la anterior", "agentic"),
        ("estrategia de puja de Menorca", "agentic"),
        ("conversiones de Costa del Sol", "agentic"),
        
        # MULTI_AGENT
        ("analiza la campaña de Baqueira", "multi_agent"),
        ("¿cómo está Costa del Sol?", "multi_agent"),
        ("dame un reporte completo de Ibiza", "multi_agent"),
    ]
    
    correct = 0
    total = len(test_cases)
    
    print("\n📋 RESULTADOS:\n")
    
    for query, expected in test_cases:
        result = router_v4.classify(query)
        is_correct = result.category == expected
        
        status = "✅" if is_correct else "❌"
        print(f"{status} Query: '{query[:50]}...'")
        print(f"   Expected: {expected}, Got: {result.category}")
        
        if is_correct:
            correct += 1
        else:
            print(f"   ⚠️ Reasoning: {result.reasoning}")
        
        print()
    
    print("="*60)
    print(f"📊 Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    print("="*60)
    
    if correct == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
    else:
        print(f"\n⚠️ {total - correct} tests fallaron.")