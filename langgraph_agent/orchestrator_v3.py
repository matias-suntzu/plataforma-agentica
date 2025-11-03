"""
Orchestrator V3 - Día 3
Orchestrator con Guardrails, Anomaly Detection y Caching

MEJORAS vs V2:
- Guardrails de entrada y salida
- Rate limiting por usuario
- Anomaly detection automático
- Caching de resultados
- Alertas automáticas
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Importar V2
from orchestrator_v2 import OrchestratorV2
from workflows_v2 import WorkflowResult

# Importar sistemas del Día 3
from guardrails import GuardrailsManager, ValidationResult
from anomaly_detector import AnomalyDetector, AnomalySeverity
from caching_system import CacheManager, QueryCache, ToolCache

load_dotenv()


class OrchestratorV3(OrchestratorV2):
    """
    Orchestrator V3 con robustez de producción.
    """
    
    def __init__(
        self,
        enable_logging: bool = True,
        enable_guardrails: bool = True,
        enable_caching: bool = True,
        enable_anomaly_detection: bool = True
    ):
        """
        Args:
            enable_logging: Habilitar logging estructurado
            enable_guardrails: Habilitar guardrails
            enable_caching: Habilitar sistema de caché
            enable_anomaly_detection: Habilitar detección de anomalías
        """
        
        # Inicializar V2
        super().__init__(enable_logging=enable_logging)
        
        print("🔒 Inicializando sistemas de seguridad...")
        
        # Guardrails
        self.enable_guardrails = enable_guardrails
        if self.enable_guardrails:
            self.guardrails = GuardrailsManager()
            print("   ✅ Guardrails activados")
        
        # Caching
        self.enable_caching = enable_caching
        if self.enable_caching:
            self.cache_manager = CacheManager(cache_dir="cache", default_ttl=1800)
            self.query_cache = QueryCache(self.cache_manager, ttl=1800)
            self.tool_cache = ToolCache(self.cache_manager, ttl=3600)
            print("   ✅ Sistema de caché activado")
        
        # Anomaly Detection
        self.enable_anomaly_detection = enable_anomaly_detection
        if self.enable_anomaly_detection:
            self.anomaly_detector = AnomalyDetector(
                cpa_threshold=50.0,
                ctr_min_threshold=0.5,
                spend_threshold=1000.0
            )
            print("   ✅ Anomaly Detection activado")
        
        print("✅ Orchestrator V3 listo (PRODUCCIÓN)\n")
    
    def process_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        user_id: str = "default",
        force_workflow: Optional[str] = None,
        skip_cache: bool = False
    ) -> WorkflowResult:
        """
        Procesa una consulta con todos los sistemas de seguridad.
        
        Args:
            query: La consulta del usuario
            thread_id: ID del thread
            user_id: ID del usuario (para rate limiting)
            force_workflow: Forzar workflow específico
            skip_cache: Saltarse el caché
            
        Returns:
            WorkflowResult
        """
        
        start_time = datetime.now()
        
        # Generar thread_id si no existe
        if not thread_id:
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*70)
        print(f"📥 NUEVA CONSULTA (V3)")
        print(f"   Query: '{query}'")
        print(f"   User ID: {user_id}")
        print(f"   Thread ID: {thread_id}")
        print("="*70)
        
        # ===== PASO 1: GUARDRAILS DE ENTRADA =====
        if self.enable_guardrails:
            validation = self.guardrails.validate_input(query, user_id)
            
            if not validation.is_valid:
                print(f"\n🚫 BLOQUEADO POR GUARDRAILS")
                print(f"   Razón: {validation.reason}")
                print(f"   Severidad: {validation.severity}")
                
                return WorkflowResult(
                    content=f"❌ {validation.reason}",
                    workflow_type="blocked",
                    metadata={
                        "blocked_by": "input_guardrails",
                        "severity": validation.severity,
                        "reason": validation.reason
                    }
                )
        
        # ===== PASO 2: VERIFICAR CACHÉ =====
        if self.enable_caching and not skip_cache:
            cached_response = self.query_cache.get_cached_response(query)
            
            if cached_response:
                print("\n⚡ RESPUESTA DESDE CACHÉ")
                
                elapsed_time = (datetime.now() - start_time).total_seconds()
                
                return WorkflowResult(
                    content=cached_response,
                    workflow_type="cached",
                    metadata={
                        "cache_hit": True,
                        "elapsed_time": elapsed_time
                    }
                )
        
        # ===== PASO 3: PROCESAR CON V2 =====
        result = super().process_query(query, thread_id, force_workflow)
        
        # ===== PASO 4: GUARDRAILS DE SALIDA =====
        if self.enable_guardrails:
            output_validation = self.guardrails.validate_output(result.content)
            
            if not output_validation.is_valid:
                print(f"\n🚫 RESPUESTA BLOQUEADA")
                print(f"   Razón: {output_validation.reason}")
                
                return WorkflowResult(
                    content="❌ La respuesta fue bloqueada por razones de seguridad.",
                    workflow_type="blocked",
                    metadata={
                        "blocked_by": "output_guardrails",
                        "reason": output_validation.reason
                    }
                )
        
        # ===== PASO 5: DETECCIÓN DE ANOMALÍAS =====
        if self.enable_anomaly_detection and result.workflow_type in ["agentic", "sequential"]:
            anomalies_detected = self._check_for_anomalies(result)
            
            if anomalies_detected:
                print(f"\n⚠️  {len(anomalies_detected)} ANOMALÍAS DETECTADAS")
                
                # Agregar resumen de anomalías a la respuesta
                anomalies_summary = self.anomaly_detector.generate_summary_report()
                result.content += f"\n\n---\n\n{anomalies_summary}"
                
                # Enviar alertas críticas
                critical_anomalies = [a for a in anomalies_detected if a.severity == AnomalySeverity.CRITICAL]
                if critical_anomalies:
                    self._send_critical_alerts(critical_anomalies)
        
        # ===== PASO 6: CACHEAR RESPUESTA =====
        if self.enable_caching and result.workflow_type not in ["error", "blocked"]:
            self.query_cache.cache_response(query, result.content)
            print("\n💾 Respuesta cacheada")
        
        return result
    
    def _check_for_anomalies(self, result: WorkflowResult) -> list:
        """Verifica si hay anomalías en los datos de la respuesta."""
        
        # Intentar extraer métricas del metadata o contenido
        metrics_data = result.metadata.get('metrics_data')
        
        if not metrics_data:
            # Intentar extraer de herramientas usadas
            # (Esto requeriría acceso al resultado de las herramientas)
            return []
        
        anomalies = self.anomaly_detector.analyze_campaign_metrics(metrics_data)
        
        return anomalies
    
    def _send_critical_alerts(self, anomalies: list):
        """Envía alertas para anomalías críticas."""
        
        print("\n🚨 ENVIANDO ALERTAS CRÍTICAS")
        
        for anomaly in anomalies:
            alert_message = anomaly.format_alert_message()
            
            print(f"\n{alert_message}")
            
            # Aquí se podría integrar con Slack, email, PagerDuty, etc.
            # Por ahora solo logging
    
    def get_system_status(self) -> dict:
        """Retorna el estado de todos los sistemas."""
        
        status = {
            "orchestrator": "V3",
            "timestamp": datetime.now().isoformat(),
            "systems": {}
        }
        
        # Métricas de workflows
        status["systems"]["workflows"] = self.get_metrics()
        
        # Estadísticas de caché
        if self.enable_caching:
            status["systems"]["cache"] = self.cache_manager.get_stats()
        
        # Violaciones de guardrails
        if self.enable_guardrails:
            recent_violations = self.guardrails.get_violations(last_n=5)
            status["systems"]["guardrails"] = {
                "total_violations": len(self.guardrails.violations_log),
                "recent": recent_violations
            }
        
        # Anomalías detectadas
        if self.enable_anomaly_detection:
            status["systems"]["anomaly_detection"] = {
                "total_anomalies": len(self.anomaly_detector.detected_anomalies),
                "critical": len(self.anomaly_detector.get_critical_anomalies())
            }
        
        return status
    
    def print_system_status(self):
        """Imprime el estado de todos los sistemas."""
        
        status = self.get_system_status()
        
        print("\n" + "="*70)
        print("🔍 ESTADO DEL SISTEMA V3")
        print("="*70)
        
        # Workflows
        workflows = status["systems"]["workflows"]
        print(f"\n📊 WORKFLOWS:")
        for wf_type, data in workflows.items():
            if data["total_queries"] > 0:
                print(f"   {wf_type}: {data['total_queries']} queries, {data['avg_time']:.2f}s avg")
        
        # Caché
        if "cache" in status["systems"]:
            cache = status["systems"]["cache"]
            print(f"\n💾 CACHÉ:")
            print(f"   Entradas: {cache['total_entries']}")
            print(f"   Hit Rate: {cache['hit_rate']}%")
            print(f"   Hits: {cache['hits']} | Misses: {cache['misses']}")
        
        # Guardrails
        if "guardrails" in status["systems"]:
            guardrails = status["systems"]["guardrails"]
            print(f"\n🔒 GUARDRAILS:")
            print(f"   Total violaciones: {guardrails['total_violations']}")
        
        # Anomalías
        if "anomaly_detection" in status["systems"]:
            anomalies = status["systems"]["anomaly_detection"]
            print(f"\n⚠️  ANOMALÍAS:")
            print(f"   Total detectadas: {anomalies['total_anomalies']}")
            print(f"   Críticas: {anomalies['critical']}")
        
        print("="*70)
    
    def shutdown(self):
        """Limpieza al cerrar el orchestrator."""
        
        print("\n🛑 Cerrando Orchestrator V3...")
        
        # Guardar caché
        if self.enable_caching:
            self.cache_manager.save_to_disk()
        
        # Guardar logs de guardrails
        if self.enable_guardrails:
            self.guardrails.save_violations_log()
        
        # Guardar anomalías
        if self.enable_anomaly_detection:
            self.anomaly_detector.save_to_file()
        
        # Mostrar estado final
        self.print_system_status()
        
        print("✅ Orchestrator V3 cerrado correctamente")


# Demo
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        print("\n🎯 DEMO ORCHESTRATOR V3\n")
        
        orch = OrchestratorV3()
        
        queries = [
            "lista todas las campañas",
            "dame el TOP 3 de Baqueira",
            "¿cuál es el clima hoy?",  # Bloqueada por guardrails
            "lista todas las campañas",  # Cache hit
        ]
        
        for query in queries:
            result = orch.process_query(query, user_id="demo_user")
            print(f"\nResultado: {result.workflow_type}")
            print("-"*70)
        
        # Estado final
        orch.print_system_status()
        orch.shutdown()
    
    else:
        print("\nUso: python orchestrator_v3.py demo")