"""
Anomaly Detector - Día 3
Sistema de detección de anomalías en métricas de Meta Ads

FUNCIONALIDADES:
1. Detecta gastos inusuales
2. Detecta CPAs anormalmente altos
3. Detecta CTRs anormalmente bajos
4. Alertas automáticas

USO:
    from anomaly_detector import AnomalyDetector
    
    detector = AnomalyDetector(cpa_threshold=50.0)
    anomalies = detector.analyze_campaign_metrics(metrics_data)
    report = detector.generate_summary_report()
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AnomalyType(Enum):
    """Tipos de anomalías detectables."""
    HIGH_CPA = "high_cpa"
    HIGH_SPEND = "high_spend"
    LOW_CTR = "low_ctr"
    LOW_CONVERSIONS = "low_conversions"
    SUDDEN_SPIKE = "sudden_spike"
    SUDDEN_DROP = "sudden_drop"


class AnomalySeverity(Enum):
    """Severidad de la anomalía."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """Representa una anomalía detectada."""
    type: AnomalyType
    severity: AnomalySeverity
    metric_name: str
    current_value: float
    expected_range: tuple
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    ad_id: Optional[str] = None
    ad_name: Optional[str] = None
    description: str = ""
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Convierte la anomalía a diccionario."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "expected_range": self.expected_range,
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "ad_id": self.ad_id,
            "ad_name": self.ad_name,
            "description": self.description,
            "timestamp": self.timestamp
        }
    
    def format_alert_message(self) -> str:
        """Formatea un mensaje de alerta legible."""
        
        severity_emoji = {
            AnomalySeverity.LOW: "ℹ️",
            AnomalySeverity.MEDIUM: "⚠️",
            AnomalySeverity.HIGH: "🔴",
            AnomalySeverity.CRITICAL: "🚨"
        }
        
        emoji = severity_emoji.get(self.severity, "⚠️")
        
        message = f"{emoji} **ALERTA: {self.type.value.upper().replace('_', ' ')}**\n\n"
        
        if self.campaign_name:
            message += f"**Campaña:** {self.campaign_name}\n"
        if self.ad_name:
            message += f"**Anuncio:** {self.ad_name}\n"
        
        message += f"**Métrica:** {self.metric_name}\n"
        message += f"**Valor actual:** {self.current_value:.2f}\n"
        message += f"**Rango esperado:** {self.expected_range[0]:.2f} - {self.expected_range[1]:.2f}\n"
        message += f"**Severidad:** {self.severity.value.upper()}\n\n"
        message += f"**Descripción:** {self.description}\n"
        
        return message


class AnomalyDetector:
    """
    Detector de anomalías en métricas de Meta Ads.
    
    Ejemplo:
        detector = AnomalyDetector(
            cpa_threshold=50.0,
            ctr_min_threshold=0.5,
            spend_threshold=1000.0
        )
        
        anomalies = detector.analyze_campaign_metrics(metrics_data)
        
        for anomaly in anomalies:
            print(anomaly.format_alert_message())
    """
    
    def __init__(
        self,
        cpa_threshold: float = 50.0,
        ctr_min_threshold: float = 0.5,
        spend_threshold: float = 1000.0,
        conversions_min: int = 1
    ):
        """
        Args:
            cpa_threshold: CPA máximo aceptable (euros)
            ctr_min_threshold: CTR mínimo aceptable (%)
            spend_threshold: Gasto máximo diario aceptable (euros)
            conversions_min: Conversiones mínimas esperadas
        """
        self.cpa_threshold = cpa_threshold
        self.ctr_min_threshold = ctr_min_threshold
        self.spend_threshold = spend_threshold
        self.conversions_min = conversions_min
        
        self.detected_anomalies: List[Anomaly] = []
    
    def analyze_ad_metrics(self, ad_data: dict, campaign_name: str = None) -> List[Anomaly]:
        """
        Analiza métricas de un anuncio y detecta anomalías.
        
        Args:
            ad_data: Diccionario con métricas del anuncio
                    Debe contener: clicks, impressions, spend, ctr, cpa, conversiones
            campaign_name: Nombre de la campaña (opcional)
            
        Returns:
            Lista de anomalías detectadas
        """
        
        anomalies = []
        
        ad_id = ad_data.get('ad_id')
        ad_name = ad_data.get('ad_name', 'N/A')
        
        # 1. Detectar CPA alto
        cpa = ad_data.get('cpa', 0)
        if cpa > self.cpa_threshold:
            severity = self._calculate_severity(cpa, self.cpa_threshold, factor=2)
            
            anomalies.append(Anomaly(
                type=AnomalyType.HIGH_CPA,
                severity=severity,
                metric_name="CPA",
                current_value=cpa,
                expected_range=(0, self.cpa_threshold),
                campaign_name=campaign_name,
                ad_id=ad_id,
                ad_name=ad_name,
                description=f"El CPA de {cpa:.2f}€ excede el umbral de {self.cpa_threshold}€"
            ))
        
        # 2. Detectar CTR bajo
        ctr = ad_data.get('ctr', 0)
        if 0 < ctr < self.ctr_min_threshold:
            severity = self._calculate_severity_inverse(ctr, self.ctr_min_threshold)
            
            anomalies.append(Anomaly(
                type=AnomalyType.LOW_CTR,
                severity=severity,
                metric_name="CTR",
                current_value=ctr,
                expected_range=(self.ctr_min_threshold, 10.0),
                campaign_name=campaign_name,
                ad_id=ad_id,
                ad_name=ad_name,
                description=f"El CTR de {ctr:.2f}% está por debajo del mínimo de {self.ctr_min_threshold}%"
            ))
        
        # 3. Detectar gasto alto
        spend = ad_data.get('spend', 0)
        if spend > self.spend_threshold:
            severity = self._calculate_severity(spend, self.spend_threshold, factor=1.5)
            
            anomalies.append(Anomaly(
                type=AnomalyType.HIGH_SPEND,
                severity=severity,
                metric_name="Spend",
                current_value=spend,
                expected_range=(0, self.spend_threshold),
                campaign_name=campaign_name,
                ad_id=ad_id,
                ad_name=ad_name,
                description=f"El gasto de {spend:.2f}€ excede el umbral de {self.spend_threshold}€"
            ))
        
        # 4. Detectar conversiones bajas (con gasto > 100€)
        conversions = ad_data.get('conversiones', 0)
        if spend > 100 and conversions < self.conversions_min:
            anomalies.append(Anomaly(
                type=AnomalyType.LOW_CONVERSIONS,
                severity=AnomalySeverity.HIGH,
                metric_name="Conversiones",
                current_value=conversions,
                expected_range=(self.conversions_min, 100),
                campaign_name=campaign_name,
                ad_id=ad_id,
                ad_name=ad_name,
                description=f"Solo {conversions} conversión(es) con un gasto de {spend:.2f}€"
            ))
        
        # Guardar anomalías detectadas
        self.detected_anomalies.extend(anomalies)
        
        return anomalies
    
    def analyze_campaign_metrics(self, metrics_data: dict) -> List[Anomaly]:
        """
        Analiza métricas de toda una campaña.
        
        Args:
            metrics_data: Diccionario con metadata y data de anuncios
                         Formato: {"metadata": {...}, "data": [{ad1}, {ad2}, ...]}
            
        Returns:
            Lista de anomalías detectadas
        """
        
        all_anomalies = []
        
        metadata = metrics_data.get('metadata', {})
        campaign_name = metadata.get('report_title', 'N/A')
        
        data = metrics_data.get('data', [])
        
        for ad in data:
            anomalies = self.analyze_ad_metrics(ad, campaign_name)
            all_anomalies.extend(anomalies)
        
        return all_anomalies
    
    def _calculate_severity(self, current: float, threshold: float, factor: float = 2.0) -> AnomalySeverity:
        """
        Calcula la severidad basada en cuánto excede el umbral.
        
        Args:
            current: Valor actual
            threshold: Umbral
            factor: Factor multiplicador para severidad
        
        Returns:
            AnomalySeverity
        """
        
        ratio = current / threshold
        
        if ratio > factor * 2:
            return AnomalySeverity.CRITICAL
        elif ratio > factor:
            return AnomalySeverity.HIGH
        elif ratio > 1.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _calculate_severity_inverse(self, current: float, threshold: float) -> AnomalySeverity:
        """Calcula severidad para métricas donde bajo es malo (ej: CTR)."""
        
        ratio = current / threshold
        
        if ratio < 0.25:
            return AnomalySeverity.CRITICAL
        elif ratio < 0.5:
            return AnomalySeverity.HIGH
        elif ratio < 0.75:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def get_critical_anomalies(self) -> List[Anomaly]:
        """Retorna solo anomalías críticas."""
        return [a for a in self.detected_anomalies if a.severity == AnomalySeverity.CRITICAL]
    
    def get_anomalies_by_type(self, anomaly_type: AnomalyType) -> List[Anomaly]:
        """Retorna anomalías de un tipo específico."""
        return [a for a in self.detected_anomalies if a.type == anomaly_type]
    
    def generate_summary_report(self) -> str:
        """Genera un reporte resumen de todas las anomalías."""
        
        if not self.detected_anomalies:
            return "✅ No se detectaron anomalías."
        
        # Agrupar por severidad
        by_severity = {
            AnomalySeverity.CRITICAL: [],
            AnomalySeverity.HIGH: [],
            AnomalySeverity.MEDIUM: [],
            AnomalySeverity.LOW: []
        }
        
        for anomaly in self.detected_anomalies:
            by_severity[anomaly.severity].append(anomaly)
        
        report = f"🔍 **REPORTE DE ANOMALÍAS**\n\n"
        report += f"Total detectadas: {len(self.detected_anomalies)}\n\n"
        
        for severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH, AnomalySeverity.MEDIUM, AnomalySeverity.LOW]:
            anomalies = by_severity[severity]
            if anomalies:
                emoji = {
                    AnomalySeverity.CRITICAL: "🚨",
                    AnomalySeverity.HIGH: "🔴",
                    AnomalySeverity.MEDIUM: "⚠️",
                    AnomalySeverity.LOW: "ℹ️"
                }[severity]
                
                report += f"{emoji} **{severity.value.upper()}:** {len(anomalies)}\n"
                
                for anomaly in anomalies[:3]:  # Mostrar solo las primeras 3
                    report += f"   • {anomaly.type.value}: {anomaly.metric_name} = {anomaly.current_value:.2f}\n"
                
                if len(anomalies) > 3:
                    report += f"   ... y {len(anomalies) - 3} más\n"
                
                report += "\n"
        
        return report
    
    def save_to_file(self, filepath: str = "anomalies_detected.jsonl"):
        """Guarda las anomalías en un archivo JSONL."""
        
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                for anomaly in self.detected_anomalies:
                    f.write(json.dumps(anomaly.to_dict(), ensure_ascii=False) + "\n")
            
            print(f"✅ {len(self.detected_anomalies)} anomalías guardadas en {filepath}")
            return True
        
        except Exception as e:
            print(f"❌ Error al guardar anomalías: {e}")
            return False
    
    def clear(self):
        """Limpia las anomalías detectadas."""
        self.detected_anomalies = []


# Tests
if __name__ == "__main__":
    print("🧪 Testing Anomaly Detector...\n")
    
    detector = AnomalyDetector(
        cpa_threshold=30.0,
        ctr_min_threshold=1.0,
        spend_threshold=500.0
    )
    
    # Datos de prueba
    test_ad_1 = {
        "ad_id": "123",
        "ad_name": "Test Ad - Alto CPA",
        "clicks": 100,
        "impressions": 10000,
        "spend": 600,
        "ctr": 1.0,
        "cpa": 60.0,
        "conversiones": 10
    }
    
    test_ad_2 = {
        "ad_id": "124",
        "ad_name": "Test Ad - CTR Bajo",
        "clicks": 10,
        "impressions": 5000,
        "spend": 200,
        "ctr": 0.2,
        "cpa": 20.0,
        "conversiones": 10
    }
    
    test_ad_3 = {
        "ad_id": "125",
        "ad_name": "Test Ad - Sin conversiones",
        "clicks": 50,
        "impressions": 3000,
        "spend": 150,
        "ctr": 1.67,
        "cpa": 0,
        "conversiones": 0
    }
    
    # Analizar
    print("Analizando anuncios de prueba...\n")
    
    anomalies_1 = detector.analyze_ad_metrics(test_ad_1, "Campaña Test")
    anomalies_2 = detector.analyze_ad_metrics(test_ad_2, "Campaña Test")
    anomalies_3 = detector.analyze_ad_metrics(test_ad_3, "Campaña Test")
    
    # Reporte
    print(detector.generate_summary_report())
    
    # Mostrar detalles de anomalías críticas
    critical = detector.get_critical_anomalies()
    if critical:
        print("\n🚨 ANOMALÍAS CRÍTICAS:\n")
        for anomaly in critical:
            print(anomaly.format_alert_message())
            print("-" * 60)
    
    print("\n✅ Tests completados")