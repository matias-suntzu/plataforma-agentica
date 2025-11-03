"""
Metrics Collector - Bonus
Sistema avanzado de recolección y análisis de métricas

FUNCIONALIDADES:
1. Métricas en tiempo real
2. Análisis de tendencias
3. Generación de reportes
4. Alertas automáticas
5. Exportación a diferentes formatos
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict
import statistics


@dataclass
class MetricSnapshot:
    """Snapshot de métricas en un momento dado."""
    timestamp: str
    total_queries: int
    queries_by_workflow: Dict[str, int]
    avg_latency: float
    cache_hit_rate: float
    active_violations: int
    active_anomalies: int
    cost_estimate: float


class MetricsCollector:
    """
    Colector avanzado de métricas del sistema.
    
    Uso:
        collector = MetricsCollector()
        snapshot = collector.collect_snapshot()
        report = collector.generate_report(hours=24)
    """
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.snapshots_file = self.base_path / "metrics_snapshots.jsonl"
    
    def _load_jsonl(self, filename: str) -> List[dict]:
        """Carga un archivo JSONL."""
        filepath = self.base_path / filename
        
        if not filepath.exists():
            return []
        
        data = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        except Exception as e:
            print(f"Error loading {filename}: {e}")
        
        return data
    
    def collect_snapshot(self) -> MetricSnapshot:
        """Recolecta un snapshot de métricas actuales."""
        
        # Cargar datos
        router_decisions = self._load_jsonl("router_v2_decisions.jsonl")
        metrics = self._load_jsonl("orchestrator_v2_metrics.jsonl")
        violations = self._load_jsonl("guardrails_violations.jsonl")
        anomalies = self._load_jsonl("anomalies_detected.jsonl")
        
        # Calcular métricas
        queries_by_workflow = defaultdict(int)
        for decision in router_decisions:
            queries_by_workflow[decision.get('category', 'unknown')] += 1
        
        latencies = [m.get('elapsed_time', 0) for m in metrics if m.get('elapsed_time')]
        avg_latency = statistics.mean(latencies) if latencies else 0
        
        cached = sum(1 for m in metrics if m.get('workflow_type') == 'cached')
        cache_hit_rate = (cached / len(metrics) * 100) if metrics else 0
        
        # Estimar costo (aproximado)
        # Asumiendo $0.000075 por 1K tokens input, $0.0003 por 1K tokens output
        # Promedio ~500 tokens input + 200 tokens output por query
        llm_queries = len(metrics) - cached  # Queries que no usaron caché
        cost_estimate = llm_queries * ((500 * 0.000075 / 1000) + (200 * 0.0003 / 1000))
        
        snapshot = MetricSnapshot(
            timestamp=datetime.now().isoformat(),
            total_queries=len(router_decisions),
            queries_by_workflow=dict(queries_by_workflow),
            avg_latency=round(avg_latency, 2),
            cache_hit_rate=round(cache_hit_rate, 2),
            active_violations=len(violations),
            active_anomalies=len(anomalies),
            cost_estimate=round(cost_estimate, 4)
        )
        
        # Guardar snapshot
        self._save_snapshot(snapshot)
        
        return snapshot
    
    def _save_snapshot(self, snapshot: MetricSnapshot):
        """Guarda un snapshot en el archivo."""
        try:
            with open(self.snapshots_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(snapshot), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Error saving snapshot: {e}")
    
    def get_snapshots(self, hours: int = 24) -> List[MetricSnapshot]:
        """Obtiene snapshots de las últimas N horas."""
        
        if not self.snapshots_file.exists():
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        snapshots = []
        
        try:
            with open(self.snapshots_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        snapshot_time = datetime.fromisoformat(data['timestamp'])
                        
                        if snapshot_time >= cutoff_time:
                            snapshots.append(MetricSnapshot(**data))
        except Exception as e:
            print(f"Error loading snapshots: {e}")
        
        return snapshots
    
    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """Genera un reporte de métricas."""
        
        snapshots = self.get_snapshots(hours)
        
        if not snapshots:
            return {
                "error": "No hay datos disponibles",
                "period": f"últimas {hours} horas"
            }
        
        # Calcular estadísticas
        total_queries = snapshots[-1].total_queries - snapshots[0].total_queries
        
        latencies = [s.avg_latency for s in snapshots if s.avg_latency > 0]
        avg_latency = statistics.mean(latencies) if latencies else 0
        min_latency = min(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        
        cache_rates = [s.cache_hit_rate for s in snapshots]
        avg_cache_rate = statistics.mean(cache_rates) if cache_rates else 0
        
        total_cost = sum(s.cost_estimate for s in snapshots)
        
        # Queries por workflow
        workflow_totals = defaultdict(int)
        for snapshot in snapshots:
            for workflow, count in snapshot.queries_by_workflow.items():
                workflow_totals[workflow] += count
        
        return {
            "period": f"últimas {hours} horas",
            "total_snapshots": len(snapshots),
            "metrics": {
                "total_queries": total_queries,
                "queries_per_hour": round(total_queries / hours, 2),
                "latency": {
                    "avg": round(avg_latency, 2),
                    "min": round(min_latency, 2),
                    "max": round(max_latency, 2)
                },
                "cache": {
                    "avg_hit_rate": round(avg_cache_rate, 2),
                    "queries_saved": int(total_queries * avg_cache_rate / 100)
                },
                "cost": {
                    "total": round(total_cost, 4),
                    "per_query": round(total_cost / total_queries, 6) if total_queries > 0 else 0,
                    "projected_monthly": round(total_cost / hours * 24 * 30, 2)
                },
                "workflows": dict(workflow_totals)
            },
            "latest_snapshot": asdict(snapshots[-1])
        }
    
    def print_report(self, hours: int = 24):
        """Imprime un reporte formateado."""
        
        report = self.generate_report(hours)
        
        if "error" in report:
            print(f"\n❌ {report['error']}")
            return
        
        print("\n" + "="*70)
        print(f"📊 REPORTE DE MÉTRICAS - {report['period']}")
        print("="*70)
        
        metrics = report['metrics']
        
        print(f"\n📈 QUERIES:")
        print(f"   Total: {metrics['total_queries']}")
        print(f"   Por hora: {metrics['queries_per_hour']}")
        
        print(f"\n⏱️  LATENCIA:")
        print(f"   Promedio: {metrics['latency']['avg']}s")
        print(f"   Mínima: {metrics['latency']['min']}s")
        print(f"   Máxima: {metrics['latency']['max']}s")
        
        print(f"\n💾 CACHÉ:")
        print(f"   Hit rate promedio: {metrics['cache']['avg_hit_rate']}%")
        print(f"   Queries ahorradas: {metrics['cache']['queries_saved']}")
        
        print(f"\n💰 COSTO:")
        print(f"   Total: ${metrics['cost']['total']}")
        print(f"   Por query: ${metrics['cost']['per_query']}")
        print(f"   Proyección mensual: ${metrics['cost']['projected_monthly']}")
        
        print(f"\n🔀 WORKFLOWS:")
        for workflow, count in metrics['workflows'].items():
            percentage = (count / metrics['total_queries'] * 100) if metrics['total_queries'] > 0 else 0
            print(f"   {workflow}: {count} ({percentage:.1f}%)")
        
        print("\n" + "="*70)
    
    def export_to_csv(self, hours: int = 24, output_file: str = "metrics_export.csv"):
        """Exporta métricas a CSV."""
        
        snapshots = self.get_snapshots(hours)
        
        if not snapshots:
            print("❌ No hay datos para exportar")
            return
        
        try:
            import csv
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Timestamp', 'Total Queries', 'Avg Latency', 
                    'Cache Hit Rate', 'Violations', 'Anomalies', 'Cost Estimate'
                ])
                
                # Data
                for snapshot in snapshots:
                    writer.writerow([
                        snapshot.timestamp,
                        snapshot.total_queries,
                        snapshot.avg_latency,
                        snapshot.cache_hit_rate,
                        snapshot.active_violations,
                        snapshot.active_anomalies,
                        snapshot.cost_estimate
                    ])
            
            print(f"✅ Métricas exportadas a {output_file}")
        
        except Exception as e:
            print(f"❌ Error al exportar: {e}")
    
    def detect_trends(self, hours: int = 24) -> Dict[str, str]:
        """Detecta tendencias en las métricas."""
        
        snapshots = self.get_snapshots(hours)
        
        if len(snapshots) < 2:
            return {"error": "Datos insuficientes para análisis de tendencias"}
        
        # Dividir en dos mitades
        mid = len(snapshots) // 2
        first_half = snapshots[:mid]
        second_half = snapshots[mid:]
        
        # Calcular promedios
        avg_latency_1 = statistics.mean(s.avg_latency for s in first_half if s.avg_latency > 0)
        avg_latency_2 = statistics.mean(s.avg_latency for s in second_half if s.avg_latency > 0)
        
        avg_cache_1 = statistics.mean(s.cache_hit_rate for s in first_half)
        avg_cache_2 = statistics.mean(s.cache_hit_rate for s in second_half)
        
        # Detectar tendencias
        trends = {}
        
        # Latencia
        if avg_latency_2 < avg_latency_1 * 0.9:
            trends['latency'] = "📉 Mejorando (reducción >10%)"
        elif avg_latency_2 > avg_latency_1 * 1.1:
            trends['latency'] = "📈 Empeorando (aumento >10%)"
        else:
            trends['latency'] = "➡️  Estable"
        
        # Caché
        if avg_cache_2 > avg_cache_1 + 10:
            trends['cache'] = "📈 Mejorando (+10% hit rate)"
        elif avg_cache_2 < avg_cache_1 - 10:
            trends['cache'] = "📉 Empeorando (-10% hit rate)"
        else:
            trends['cache'] = "➡️  Estable"
        
        return trends


# CLI
if __name__ == "__main__":
    import sys
    
    collector = MetricsCollector()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "snapshot":
            print("\n📸 Recolectando snapshot...")
            snapshot = collector.collect_snapshot()
            print(f"✅ Snapshot guardado: {snapshot.timestamp}")
            print(f"   Queries: {snapshot.total_queries}")
            print(f"   Latencia: {snapshot.avg_latency}s")
            print(f"   Cache: {snapshot.cache_hit_rate}%")
        
        elif command == "report":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            collector.print_report(hours)
        
        elif command == "trends":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            trends = collector.detect_trends(hours)
            
            print("\n📊 ANÁLISIS DE TENDENCIAS")
            print("="*60)
            for metric, trend in trends.items():
                print(f"   {metric.title()}: {trend}")
        
        elif command == "export":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            output = sys.argv[3] if len(sys.argv) > 3 else "metrics_export.csv"
            collector.export_to_csv(hours, output)
        
        else:
            print("Comando no reconocido")
    
    else:
        print("\nUso:")
        print("  python metrics_collector.py snapshot        - Tomar snapshot")
        print("  python metrics_collector.py report [hours]  - Generar reporte")
        print("  python metrics_collector.py trends [hours]  - Análisis de tendencias")
        print("  python metrics_collector.py export [hours] [file] - Exportar a CSV")