"""
Workflows V2 - Día 2
Añade Sequential Workflow para flujos multi-paso

WORKFLOWS DISPONIBLES:
1. FastPathWorkflow (V1) - Consultas simples sin LLM
2. SequentialWorkflow (NUEVO) - Flujos multi-paso predefinidos
3. AgenticWorkflow (V1) - Análisis complejos con razonamiento
4. ConversationWorkflow (NUEVO) - Preguntas de seguimiento con memoria
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from workflows import WorkflowResult, FastPathWorkflow, AgenticWorkflow


class SequentialWorkflow:
    """
    Workflow SEQUENTIAL - Flujos multi-paso predefinidos.
    
    Casos de uso:
    - "Genera reporte Y envía a Slack"
    - "Analiza campañas Y crea resumen"
    - Cualquier flujo con pasos definidos en secuencia
    
    Ejemplo:
        workflow = SequentialWorkflow(url, key, agent)
        result = workflow.execute("genera reporte de Baqueira y envíalo a Slack", "thread_123")
    """
    
    def __init__(self, langserve_url: str, api_key: str, agent_app):
        self.langserve_url = langserve_url
        self.api_key = api_key
        self.agent_app = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """
        Ejecuta un flujo secuencial basado en la consulta.
        
        Args:
            query: La consulta del usuario
            thread_id: ID del thread para memoria
            
        Returns:
            WorkflowResult con el resultado del flujo completo
        """
        print(f"\n🔗 SEQUENTIAL WORKFLOW")
        print(f"   Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        
        # Detectar tipo de flujo secuencial
        query_lower = query.lower()
        
        # FLUJO 1: Generar reporte + Enviar
        if self._is_report_and_send(query_lower):
            return self._execute_report_and_send(query, thread_id)
        
        # FLUJO 2: Analizar + Resumir
        elif self._is_analyze_and_summarize(query_lower):
            return self._execute_analyze_and_summarize(query, thread_id)
        
        # FLUJO 3: Comparar + Alertar
        elif self._is_compare_and_alert(query_lower):
            return self._execute_compare_and_alert(query, thread_id)
        
        # Fallback: Usar agente genérico si no coincide patrón
        else:
            print("   ⚠️  Patrón secuencial no reconocido, usando agente genérico")
            return self._fallback_to_agentic(query, thread_id)
    
    def _is_report_and_send(self, query: str) -> bool:
        """Detecta: 'genera reporte ... y envía/manda'"""
        keywords_report = ["genera", "crea", "reporte", "informe", "slides"]
        keywords_send = ["envía", "manda", "slack", "email"]
        
        has_report = any(kw in query for kw in keywords_report)
        has_send = any(kw in query for kw in keywords_send)
        has_and = " y " in query or " y luego " in query
        
        return has_report and has_send and has_and
    
    def _is_analyze_and_summarize(self, query: str) -> bool:
        """Detecta: 'analiza ... y resume/crea resumen'"""
        keywords_analyze = ["analiza", "revisa", "estudia"]
        keywords_summarize = ["resume", "resumen", "sintetiza", "crea"]
        
        has_analyze = any(kw in query for kw in keywords_analyze)
        has_summarize = any(kw in query for kw in keywords_summarize)
        has_and = " y " in query
        
        return has_analyze and has_summarize and has_and
    
    def _is_compare_and_alert(self, query: str) -> bool:
        """Detecta: 'compara ... y alerta/avisa si'"""
        keywords_compare = ["compara", "comparar", "diferencia"]
        keywords_alert = ["alerta", "avisa", "notifica", "slack"]
        
        has_compare = any(kw in query for kw in keywords_compare)
        has_alert = any(kw in query for kw in keywords_alert)
        
        return has_compare and has_alert
    
    def _execute_report_and_send(self, query: str, thread_id: str) -> WorkflowResult:
        """
        Flujo: Analizar datos → Generar reporte → Enviar a Slack
        """
        print("\n   📊 FLUJO: Reporte + Envío")
        steps_log = []
        
        try:
            # PASO 1: Extraer información de la campaña
            print("   1️⃣ Extrayendo datos de campaña...")
            campaign_name = self._extract_campaign_name(query)
            
            if not campaign_name:
                return WorkflowResult(
                    content="❌ No pude identificar la campaña en tu consulta. Por favor especifica el nombre.",
                    workflow_type="sequential",
                    metadata={"error": "campaign_not_found"}
                )
            
            steps_log.append(f"Campaña identificada: {campaign_name}")
            
            # PASO 2: Buscar ID de campaña
            print(f"   2️⃣ Buscando ID de campaña '{campaign_name}'...")
            campaign_id = self._buscar_id_campana(campaign_name)
            
            if not campaign_id or campaign_id == "None":
                return WorkflowResult(
                    content=f"❌ No encontré la campaña '{campaign_name}' en Meta Ads.",
                    workflow_type="sequential",
                    metadata={"error": "campaign_id_not_found"}
                )
            
            steps_log.append(f"ID encontrado: {campaign_id}")
            
            # PASO 3: Obtener métricas
            print(f"   3️⃣ Obteniendo métricas de campaña...")
            metricas = self._obtener_metricas(campaign_id)
            
            if not metricas:
                return WorkflowResult(
                    content=f"❌ No pude obtener métricas de la campaña {campaign_id}.",
                    workflow_type="sequential",
                    metadata={"error": "metrics_not_found"}
                )
            
            steps_log.append(f"Métricas obtenidas: {len(metricas.get('data', []))} anuncios")
            
            # PASO 4: Generar reporte en Slides
            print(f"   4️⃣ Generando reporte en Google Slides...")
            
            # Crear resumen ejecutivo
            resumen = self._crear_resumen_ejecutivo(metricas)
            
            # Llamar a herramienta de Slides
            slides_url = self._generar_slides(resumen, json.dumps(metricas))
            
            if not slides_url or "Error" in slides_url:
                steps_log.append("Reporte: Error al generar")
                # Continuar con Slack aunque falle Slides
                slides_info = f"⚠️ Error al generar Slides: {slides_url}"
            else:
                steps_log.append(f"Reporte generado: {slides_url}")
                slides_info = f"✅ Reporte generado:\n{slides_url}"
            
            # PASO 5: Enviar a Slack
            print(f"   5️⃣ Enviando notificación a Slack...")
            
            slack_message = f"""
📊 **Reporte de Campaña Generado**

**Campaña:** {campaign_name}
**ID:** {campaign_id}
**Anuncios analizados:** {len(metricas.get('data', []))}

{slides_info}

*Generado automáticamente por el Agente de Meta Ads*
            """.strip()
            
            slack_result = self._enviar_slack(slack_message)
            steps_log.append(f"Slack: {slack_result}")
            
            # PASO 6: Respuesta final
            final_message = f"""
✅ **Flujo completado exitosamente**

**Pasos ejecutados:**
1. ✅ Campaña identificada: {campaign_name}
2. ✅ ID encontrado: {campaign_id}
3. ✅ Métricas obtenidas: {len(metricas.get('data', []))} anuncios
4. {slides_info}
5. ✅ Notificación enviada a Slack

**Resumen de métricas:**
{resumen}
            """.strip()
            
            return WorkflowResult(
                content=final_message,
                workflow_type="sequential",
                metadata={
                    "steps": steps_log,
                    "campaign_id": campaign_id,
                    "slides_url": slides_url if "Error" not in slides_url else None,
                    "total_ads": len(metricas.get('data', []))
                }
            )
        
        except Exception as e:
            print(f"   ❌ Error en flujo secuencial: {e}")
            return WorkflowResult(
                content=f"❌ Error durante el flujo secuencial: {str(e)}",
                workflow_type="sequential",
                metadata={"error": str(e), "steps": steps_log}
            )
    
    def _execute_analyze_and_summarize(self, query: str, thread_id: str) -> WorkflowResult:
        """Flujo: Analizar campañas → Crear resumen"""
        print("\n   📈 FLUJO: Análisis + Resumen")
        
        # Por ahora, delegamos al agente
        # En el futuro, se puede implementar un flujo específico
        return self._fallback_to_agentic(query, thread_id)
    
    def _execute_compare_and_alert(self, query: str, thread_id: str) -> WorkflowResult:
        """Flujo: Comparar períodos → Alertar si anomalía"""
        print("\n   ⚖️  FLUJO: Comparación + Alerta")
        
        # Por ahora, delegamos al agente
        return self._fallback_to_agentic(query, thread_id)
    
    def _fallback_to_agentic(self, query: str, thread_id: str) -> WorkflowResult:
        """Fallback: Usar agente genérico si no hay flujo específico."""
        print("   🤖 Usando agente genérico como fallback")
        
        agentic = AgenticWorkflow(self.agent_app)
        result = agentic.execute(query, thread_id)
        
        # Cambiar el workflow_type para tracking
        result.workflow_type = "sequential_fallback"
        
        return result
    
    # ========== FUNCIONES HELPER ==========
    
    def _extract_campaign_name(self, query: str) -> Optional[str]:
        """Extrae el nombre de la campaña de la consulta."""
        # Palabras clave comunes
        keywords = ["baqueira", "costa", "tenerife", "verano", "invierno"]
        
        query_lower = query.lower()
        
        for keyword in keywords:
            if keyword in query_lower:
                return keyword
        
        # Si no encuentra keyword, intenta extraer palabra después de "de"
        if " de " in query_lower:
            parts = query_lower.split(" de ")
            if len(parts) > 1:
                # Tomar primera palabra después de "de"
                candidate = parts[1].split()[0].strip()
                if len(candidate) > 3:
                    return candidate
        
        return None
    
    def _buscar_id_campana(self, nombre: str) -> Optional[str]:
        """Llama a la herramienta BuscarIdCampanaInput."""
        try:
            url = f"{self.langserve_url}/buscaridcampana/invoke"
            headers = {
                "Content-Type": "application/json",
                "X-Tool-Api-Key": self.api_key
            }
            payload = {
                "input": {"nombre_campana": nombre}
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json().get('output', {})
                return result.get('id_campana')
            
            return None
        
        except Exception as e:
            print(f"      ❌ Error al buscar ID: {e}")
            return None
    
    def _obtener_metricas(self, campaign_id: str) -> Optional[dict]:
        """Llama a ObtenerAnunciosPorRendimientoInput."""
        try:
            url = f"{self.langserve_url}/obteneranunciosrendimiento/invoke"
            headers = {
                "Content-Type": "application/json",
                "X-Tool-Api-Key": self.api_key
            }
            payload = {
                "input": {
                    "campana_id": campaign_id,
                    "date_preset": "last_month",
                    "limite": 5
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json().get('output', {})
                datos_json = result.get('datos_json', '{}')
                return json.loads(datos_json)
            
            return None
        
        except Exception as e:
            print(f"      ❌ Error al obtener métricas: {e}")
            return None
    
    def _crear_resumen_ejecutivo(self, metricas: dict) -> str:
        """Crea un resumen ejecutivo a partir de las métricas."""
        data = metricas.get('data', [])
        
        if not data:
            return "No hay datos disponibles para análisis."
        
        # Calcular totales
        total_clicks = sum(ad.get('clicks', 0) for ad in data)
        total_impressions = sum(ad.get('impressions', 0) for ad in data)
        total_spend = sum(ad.get('spend', 0) for ad in data)
        total_conversions = sum(ad.get('conversiones', 0) for ad in data)
        
        avg_ctr = total_clicks / total_impressions * 100 if total_impressions > 0 else 0
        avg_cpa = total_spend / total_conversions if total_conversions > 0 else 0
        
        mejor_anuncio = max(data, key=lambda x: x.get('clicks', 0))
        
        resumen = f"""
**Resumen Ejecutivo:**
- Total anuncios: {len(data)}
- Clicks totales: {total_clicks:,}
- Impresiones: {total_impressions:,}
- Gasto total: {total_spend:.2f}€
- Conversiones: {total_conversions}
- CTR promedio: {avg_ctr:.2f}%
- CPA promedio: {avg_cpa:.2f}€

**Mejor anuncio:** {mejor_anuncio.get('ad_name', 'N/A')}
- Clicks: {mejor_anuncio.get('clicks', 0):,}
- CPA: {mejor_anuncio.get('cpa', 0):.2f}€
        """.strip()
        
        return resumen
    
    def _generar_slides(self, resumen: str, datos_json: str) -> str:
        """Llama a GenerarReporteGoogleSlidesInput."""
        try:
            url = f"{self.langserve_url}/generar_reporte_slides/invoke"
            headers = {
                "Content-Type": "application/json",
                "X-Tool-Api-Key": self.api_key
            }
            payload = {
                "input": {
                    "resumen_ejecutivo": resumen,
                    "datos_tabla_json": datos_json
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json().get('output', {})
                return result.get('slides_url', 'Error: URL no disponible')
            
            return f"Error: Código {response.status_code}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _enviar_slack(self, mensaje: str) -> str:
        """Llama a EnviarAlertaSlackInput."""
        try:
            url = f"{self.langserve_url}/enviaralertaslack/invoke"
            headers = {
                "Content-Type": "application/json",
                "X-Tool-Api-Key": self.api_key
            }
            payload = {
                "input": {"mensaje": mensaje}
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json().get('output', {})
                return result.get('resultado', 'Enviado')
            
            return f"Error código {response.status_code}"
        
        except Exception as e:
            return f"Error: {str(e)}"


class ConversationWorkflow:
    """
    Workflow CONVERSACIONAL - Preguntas de seguimiento.
    Siempre usa el agente con memoria activada.
    
    Ejemplo:
        workflow = ConversationWorkflow(agent)
        result = workflow.execute("¿cuál tiene mejor CPA?", "thread_123")
    """
    
    def __init__(self, agent_app):
        self.agent = agent_app
    
    def execute(self, query: str, thread_id: str) -> WorkflowResult:
        """
        Ejecuta pregunta de seguimiento con contexto.
        
        Args:
            query: La pregunta de seguimiento
            thread_id: ID del thread (CRÍTICO para memoria)
            
        Returns:
            WorkflowResult con respuesta basada en contexto
        """
        print(f"\n💬 CONVERSATION WORKFLOW")
        print(f"   Query: '{query}'")
        print(f"   Thread ID: {thread_id}")
        print(f"   🧠 Usando memoria conversacional...")
        
        # Simplemente delegar al agente con memoria
        agentic = AgenticWorkflow(self.agent)
        result = agentic.execute(query, thread_id)
        
        # Cambiar workflow_type para tracking
        result.workflow_type = "conversation"
        
        return result


# Export para compatibilidad
__all__ = [
    'WorkflowResult',
    'FastPathWorkflow',
    'SequentialWorkflow',
    'AgenticWorkflow',
    'ConversationWorkflow'
]