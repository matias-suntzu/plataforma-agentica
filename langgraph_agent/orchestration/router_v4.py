"""
Router V4 - SIMPLIFICADO (3 categorías) + CONTEXTO CONVERSACIONAL
Reduce complejidad y mejora precisión
"""

import os
from typing import Literal, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
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
        description="Intención: 'list', 'metrics', 'config', 'compare', 'report', 'recommendation', 'continuation'"
    )


# ========== PROMPT ==========

ROUTER_V4_PROMPT = """
Eres un clasificador experto de consultas para un sistema de Meta Ads.

**📄 CONTEXTO CONVERSACIONAL:**
{conversation_context}

**🔍 CONSULTA ACTUAL:**
{query}

Clasifica la consulta en UNA de estas 3 categorías:

┌────────────────────────────────────────────────────────────────┐

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

├────────────────────────────────────────────────────────────────┤

🤖 **AGENTIC** (Con agente especializado):
   Características:
   - Requiere llamar a ConfigAgent, PerformanceAgent o RecommendationAgent
   - Necesita búsqueda de campaña por nombre
   - Métricas o configuración de UNA campaña
   - Comparaciones de períodos
   - TOP N anuncios
   - 🆕 **ANÁLISIS DE ANUNCIOS INDIVIDUALES** 🔥
   - 🆕 **COMPARACIONES DE ANUNCIOS** (identificar cuál empeoró) 🔥
   - 🆕 **"¿Qué anuncio explica X?"** → SIEMPRE PerformanceAgent 🔥
   - Recomendaciones específicas de UNA campaña
   - **CONTINUACIONES de conversaciones previas** 📄
   
   Ejemplos:
   ✅ "¿qué presupuesto tiene Baqueira?" → ConfigAgent
   ✅ "gasto de Ibiza esta semana" → PerformanceAgent
   ✅ "TOP 3 de anuncios de Costa Blanca" → PerformanceAgent
   ✅ "compara esta semana con la anterior" → PerformanceAgent
   ✅ "estrategia de puja de Menorca" → ConfigAgent
   ✅ "dame recomendaciones para Baqueira" → RecommendationAgent
   ✅ "¿cómo mejorar el CPA de Ibiza?" → RecommendationAgent
   ✅ 🔥 "¿qué anuncio ha empeorado?" → PerformanceAgent
   ✅ 🔥 "¿qué anuncio explica el cambio en el CPA?" → PerformanceAgent
   ✅ 🔥 "dame todos los anuncios de Baqueira" → PerformanceAgent
   ✅ 🔥 "¿hay algún anuncio que ha empeorado?" → PerformanceAgent
   
   **CONTINUACIONES (CRÍTICO):** 📄
   Si el asistente preguntó algo en el contexto, la respuesta del usuario es AGENTIC:
   ✅ Contexto: "¿De qué campaña?" → Usuario: "campaña de baqueira" → AGENTIC
   ✅ Contexto: "¿Cuál campaña?" → Usuario: "baqueira" → AGENTIC
   ✅ Contexto: "necesito el ID" → Usuario: "de la de ibiza" → AGENTIC
   ✅ Contexto: pregunta del bot → Usuario: "todas" → AGENTIC

├────────────────────────────────────────────────────────────────┤

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
   ✅ "análisis completo con recomendaciones de Baqueira"

└────────────────────────────────────────────────────────────────┘

🎯 REGLAS CRÍTICAS:

1. **MÁXIMA PRIORIDAD - Detección de continuaciones:** 📄
   - Si hay contexto conversacional Y el asistente hizo una pregunta → la respuesta es AGENTIC
   - Indicadores: "¿de qué campaña?", "¿cuál?", "necesito", "proporciona", "especifica"
   - Si la query es ≤4 palabras Y hay contexto → probablemente AGENTIC (continuation)

2. **🔥 NUEVA REGLA: Queries sobre ANUNCIOS → SIEMPRE AGENTIC (PerformanceAgent)**
   - Si menciona "anuncio", "anuncios", "ad", "ads" → AGENTIC
   - "¿qué anuncio...?" → AGENTIC (detected_intent: ad_analysis)
   - "¿hay algún anuncio que...?" → AGENTIC (detected_intent: ad_analysis)
   - "dame todos los anuncios" → AGENTIC (detected_intent: ad_analysis)
   - "¿cuál anuncio explica...?" → AGENTIC (detected_intent: ad_analysis)
   
3. **Prioridad de clasificación:**
   1. Queries sobre anuncios → AGENTIC (detected_intent: ad_analysis) 🔥
   2. Continuación de conversación → AGENTIC (detected_intent: continuation)
   3. Solo listar SIN métricas → SIMPLE
   4. Campaña + métricas → AGENTIC (PerformanceAgent)
   5. Campaña + config → AGENTIC (ConfigAgent)
   6. Campaña + recomendaciones → AGENTIC (RecommendationAgent)
   7. "Análisis completo" → MULTI_AGENT

4. **Palabras clave AGENTIC:**
   - Métricas: gasto, conversiones, clicks, CTR, CPM, CPC, CPA
   - Config: presupuesto, estrategia, puja, objetivo
   - Comparaciones: "compara", "vs", "versus"
   - TOP: "TOP 3", "mejores", "peores"
   - Recomendaciones: "recomienda", "optimiza", "mejora", "sugerencia", "debería"
   - 🔥 Anuncios: "anuncio", "anuncios", "ad", "ads", "empeorado", "explica"

5. **Detected Intent:**
   - 'ad_analysis' → análisis de anuncios (AGENTIC/PerformanceAgent) 🔥
   - 'continuation' → respuesta a pregunta del asistente (AGENTIC) 📄
   - 'list' → solo listar (SIMPLE)
   - 'metrics' → métricas (AGENTIC/PerformanceAgent)
   - 'config' → configuración (AGENTIC/ConfigAgent)
   - 'recommendation' → recomendaciones (AGENTIC/RecommendationAgent)
   - 'report' → reporte completo (MULTI_AGENT)

Clasifica la consulta actual considerando TODO el contexto conversacional.
"""


# ========== ROUTER ==========

class QueryRouterV4:
    """Router simplificado con 3 categorías + contexto conversacional"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.0,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        self.structured_llm = self.llm.with_structured_output(RouteQueryV4)
        self.prompt = ChatPromptTemplate.from_template(ROUTER_V4_PROMPT)
        self.chain = self.prompt | self.structured_llm
    
    def classify(self, query: str, messages: Optional[List[BaseMessage]] = None) -> RouteQueryV4:
        """
        Clasifica una consulta en 3 categorías considerando el contexto.
        
        Args:
            query: La consulta del usuario
            messages: Historial de mensajes para contexto (opcional)
            
        Returns:
            RouteQueryV4 con category, confidence, reasoning, etc.
        """
        # Preparar contexto conversacional
        conversation_context = self._prepare_context(messages)
        
        result = self.chain.invoke({
            "query": query,
            "conversation_context": conversation_context
        })
        
        # Log visual
        self._print_decision(query, result, has_context=bool(messages))
        
        return result
    
    def _prepare_context(self, messages: Optional[List[BaseMessage]]) -> str:
        """Prepara el contexto conversacional para el prompt"""
        if not messages or len(messages) == 0:
            return "Sin historial previo (primera consulta del thread)"
        
        # Tomar últimos 6 mensajes para no saturar
        recent_messages = messages[-6:] if len(messages) > 6 else messages
        
        context_lines = []
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                # Truncar mensajes muy largos
                content = msg.content[:200] if len(msg.content) > 200 else msg.content
                context_lines.append(f"👤 Usuario: {content}")
            elif isinstance(msg, AIMessage):
                # Solo primeros 150 chars para no saturar
                content = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
                context_lines.append(f"🤖 Asistente: {content}")
        
        if not context_lines:
            return "Sin historial previo (primera consulta del thread)"
        
        return "\n".join(context_lines)
    
    def _print_decision(self, query: str, result: RouteQueryV4, has_context: bool = False):
        """Imprime la decisión con formato visual"""
        emoji_map = {
            "simple": "⚡",
            "agentic": "🤖",
            "multi_agent": "🔀"
        }
        
        emoji = emoji_map.get(result.category, "❓")
        context_indicator = "🔄" if has_context else ""
        
        print(f"\n{'='*60}")
        print(f"🔀 ROUTER V4 DECISION {context_indicator}")
        print(f"{'='*60}")
        print(f"   Query: '{query}'")
        print(f"   {emoji} Category: {result.category.upper()}")
        print(f"   📊 Confidence: {result.confidence:.2f}")
        print(f"   💡 Reasoning: {result.reasoning}")
        
        if result.detected_intent:
            intent_emoji = "🔄" if result.detected_intent == "continuation" else "🎯"
            print(f"   {intent_emoji} Intent: {result.detected_intent}")
        
        print(f"{'='*60}\n")


# ========== EXPORTAR ==========

router_v4 = QueryRouterV4()