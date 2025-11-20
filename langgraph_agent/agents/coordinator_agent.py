"""
Coordinador de Agentes
Responsabilidad: Decidir qué agente especializado debe responder
"""

import os
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field


# ========== SCHEMA ==========

class RouteDecision(BaseModel):
    """Decisión de routing entre agentes"""
    agent: Literal["config", "performance", "recommendation", "multi"] = Field(
        description="Agente a usar: 'config', 'recommendation', o 'multi'"
    )
    confidence: float = Field(
        description="Confianza en la decisión (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Explicación de la decisión"
    )


# ========== PROMPT ==========

COORDINATOR_PROMPT = """
Eres un coordinador inteligente que decide qué agente especializado debe responder una query.

AGENTES DISPONIBLES:

📋 **ConfigAgent** (Configuración Técnica):
- Listados de campañas
- Búsqueda de campañas por nombre
- Presupuestos configurados (diario, lifetime)
- Estrategias de puja
- Objetivos de campaña
- Configuración de adsets (targeting, Advantage+)

📊 **PerformanceAgent** (Métricas de Rendimiento):
- Gasto real (cuánto se ha gastado)
- Impresiones, clicks, CTR
- CPM, CPC, CPA
- Conversiones y tipos
- TOP N anuncios
- Comparaciones de períodos
- 🔥 ANÁLISIS DE ANUNCIOS INDIVIDUALES
- 🔥 COMPARACIONES DE ANUNCIOS (identificar cuál empeoró)
- 🔥 "¿Qué anuncio explica X cambio?" → PerformanceAgent

💡 **RecommendationAgent** (Recomendaciones de Optimización):
- Sugerencias para mejorar CPA/CPC
- Detectar Advantage+ no activado
- Identificar presupuestos bajos
- Analizar targeting subóptimo
- Análisis de oportunidades

🔀 **MULTI** (Varios agentes):
- Análisis completo (config + rendimiento + recomendaciones)
- "¿Cómo está Baqueira?" (necesita varios)
- Reportes completos con sugerencias

REGLAS DE DECISIÓN:

1. Si menciona solo configuración → **config**
   - "presupuesto de Baqueira"
   - "estrategia de puja"
   - "lista campañas"

2. Si menciona solo rendimiento → **performance**
   - "gasto de Baqueira"
   - "conversiones de Ibiza"
   - "TOP 3 anuncios"
   - "compara esta semana con la anterior"

3. 🔥 **NUEVA REGLA: Si menciona ANUNCIOS → SIEMPRE performance**
   - "¿qué anuncio ha empeorado?" → **performance**
   - "¿hay algún anuncio que explica el cambio en CPA?" → **performance**
   - "dame todos los anuncios" → **performance**
   - "¿cuál anuncio tiene peor CPA?" → **performance**
   - "compara los anuncios" → **performance**

4. Si menciona recomendaciones/optimización → **recommendation**
   - "¿cómo mejorar el CPA?"
   - "dame recomendaciones"
   - "¿qué puedo optimizar?"
   - "sugerencias para Baqueira"
   - "¿debería activar Advantage+?"

5. Si menciona varios aspectos → **multi**
   - "analiza la campaña de Baqueira" (config + rendimiento + recomendaciones)
   - "¿cómo está Costa Blanca?" (varios)
   - "reporte completo con sugerencias"

PALABRAS CLAVE:

Config: presupuesto (configurado), estrategia, puja, objetivo, targeting, adset
Performance: gasto (real), conversiones, clicks, impresiones, CTR, CPM, CPC, CPA, compara, TOP, 🔥 anuncio, anuncios
Recommendation: recomienda, optimiza, mejora, sugerencia, debería, Advantage+, oportunidad

Query del usuario: {query}

Decide qué agente(s) usar.
"""


# ========== COORDINADOR ==========

class CoordinatorAgent:
    """Coordinador que decide qué agente usar"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.0,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        self.structured_llm = self.llm.with_structured_output(RouteDecision)
        self.prompt = ChatPromptTemplate.from_template(COORDINATOR_PROMPT)
        self.chain = self.prompt | self.structured_llm
    
    def route(self, query: str) -> RouteDecision:
        """
        Decide qué agente debe responder.
        
        Args:
            query: Query del usuario
            
        Returns:
            RouteDecision con agente, confianza y razonamiento
        """
        decision = self.chain.invoke({"query": query})
        
        # Log visual
        self._print_decision(query, decision)
        
        return decision
    
    def _print_decision(self, query: str, decision: RouteDecision):
        """Imprime la decisión con formato visual"""
        emoji_map = {
            "config": "📋",
            "performance": "📊",
            "both": "🔀"
        }
        
        emoji = emoji_map.get(decision.agent, "❓")
        
        print(f"\n{'='*60}")
        print(f"🎯 COORDINATOR DECISION")
        print(f"{'='*60}")
        print(f"   Query: '{query}'")
        print(f"   {emoji} Agent: {decision.agent.upper()}")
        print(f"   📊 Confidence: {decision.confidence:.2f}")
        print(f"   💡 Reasoning: {decision.reasoning}")
        print(f"{'='*60}\n")


# ========== EXPORTAR ==========

coordinator = CoordinatorAgent()


# ========== TESTING ==========

if __name__ == "__main__":
    print("\n🧪 Testing Coordinator...\n")
    
    test_cases = [
        # Config
        ("lista todas las campañas", "config"),
        ("¿qué presupuesto tiene Baqueira?", "config"),
        ("estrategia de puja de Ibiza", "config"),
        
        # Performance
        ("¿cuánto he gastado en Baqueira?", "performance"),
        ("TOP 3 de anuncios de Costa Blanca", "performance"),
        ("compara esta semana con la anterior", "performance"),
        ("conversiones de Ibiza", "performance"),
        
        # Both
        ("analiza la campaña de Baqueira", "both"),
        ("¿cómo está Costa del Sol?", "both"),
        ("dame un reporte completo de Menorca", "both"),
    ]
    
    correct = 0
    total = len(test_cases)
    
    print("\n📋 RESULTADOS:\n")
    
    for query, expected in test_cases:
        decision = coordinator.route(query)
        is_correct = decision.agent == expected
        
        status = "✅" if is_correct else "❌"
        print(f"{status} Query: '{query[:50]}...'")
        print(f"   Expected: {expected}, Got: {decision.agent}")
        
        if is_correct:
            correct += 1
        else:
            print(f"   ⚠️ Reasoning: {decision.reasoning}")
        
        print()
    
    print("="*60)
    print(f"📊 Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    print("="*60)
    
    if correct == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
    else:
        print(f"\n⚠️ {total - correct} tests fallaron.")