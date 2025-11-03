# 🎨 Dashboard de Observability

Sistema de monitoreo visual en tiempo real para el Agente de Meta Ads.

---

## 📦 Archivos Entregados

| # | Archivo | Descripción |
|---|---------|-------------|
| 1️⃣ | `dashboard.py` | Dashboard web interactivo (Dash + Plotly) |
| 2️⃣ | `metrics_collector.py` | Colector avanzado de métricas |

---

## 🚀 Instalación

### Dependencias Necesarias

```bash
pip install dash dash-bootstrap-components plotly
```

**Nota:** Si ya usas `plotly` para el sistema de caché, solo necesitas instalar `dash`.

---

## 📊 Dashboard Web

### Inicio Rápido

```bash
# Terminal 1: Iniciar el dashboard
python dashboard.py

# Abre tu navegador en:
http://localhost:8050
```

### Características del Dashboard

#### 1️⃣ **Métricas Principales** (Cards superiores)
```
📊 Total Queries        - Total de consultas procesadas
⚡ Latencia Promedio    - Tiempo de respuesta promedio
💾 Cache Hit Rate       - Porcentaje de queries desde caché
🚨 Anomalías Críticas   - Anomalías que requieren acción inmediata
```

#### 2️⃣ **Gráficos Interactivos**

**Distribución de Workflows** (Pie Chart)
- Muestra qué workflows se usan más
- Colores por categoría:
  - 🔵 Simple (Fast Path)
  - 🟡 Sequential (Multi-paso)
  - 🟢 Agentic (Complejo)
  - 🟣 Conversation (Seguimiento)

**Latencia por Workflow** (Bar Chart)
- Compara tiempos de respuesta
- Identifica workflows lentos
- Ayuda a optimizar

#### 3️⃣ **Listas en Tiempo Real**

**Violaciones de Guardrails**
- Últimas 5 violaciones
- Código de colores por severidad:
  - 🔴 Critical
  - 🟡 Error
  - 🔵 Warning

**Anomalías Detectadas**
- Últimas 5 anomalías
- Detalles de métricas anormales
- Severidad y descripción

### Auto-Refresh

El dashboard se actualiza automáticamente cada **5 segundos**.

---

## 📈 Metrics Collector

Herramienta CLI para análisis avanzado de métricas.

### Comandos Disponibles

#### 1. **Tomar Snapshot**

```bash
python metrics_collector.py snapshot
```

Salida:
```
📸 Recolectando snapshot...
✅ Snapshot guardado: 2025-10-31T20:30:00
   Queries: 156
   Latencia: 3.42s
   Cache: 45.2%
```

**Uso:** Ejecuta esto periódicamente (ej: cada 5 minutos con cron) para mantener historial.

---

#### 2. **Generar Reporte**

```bash
# Reporte de últimas 24 horas
python metrics_collector.py report

# Reporte de últimas 12 horas
python metrics_collector.py report 12
```

Salida:
```
======================================================================
📊 REPORTE DE MÉTRICAS - últimas 24 horas
======================================================================

📈 QUERIES:
   Total: 342
   Por hora: 14.25

⏱️  LATENCIA:
   Promedio: 3.21s
   Mínima: 0.15s
   Máxima: 15.43s

💾 CACHÉ:
   Hit rate promedio: 42.5%
   Queries ahorradas: 145

💰 COSTO:
   Total: $0.0234
   Por query: $0.000068
   Proyección mensual: $0.70

🔀 WORKFLOWS:
   simple: 145 (42.4%)
   agentic: 123 (36.0%)
   sequential: 52 (15.2%)
   conversation: 22 (6.4%)
======================================================================
```

---

#### 3. **Análisis de Tendencias**

```bash
# Detectar tendencias de últimas 24 horas
python metrics_collector.py trends

# Tendencias de últimas 6 horas
python metrics_collector.py trends 6
```

Salida:
```
📊 ANÁLISIS DE TENDENCIAS
============================================================
   Latency: 📉 Mejorando (reducción >10%)
   Cache: 📈 Mejorando (+10% hit rate)
```

**Interpretación:**
- 📉 Mejorando: Métrica ha mejorado >10%
- 📈 Empeorando: Métrica ha empeorado >10%
- ➡️  Estable: Sin cambios significativos

---

#### 4. **Exportar a CSV**

```bash
# Exportar últimas 24 horas
python metrics_collector.py export

# Exportar últimas 48 horas a archivo custom
python metrics_collector.py export 48 my_metrics.csv
```

Genera un CSV con columnas:
```
Timestamp, Total Queries, Avg Latency, Cache Hit Rate, Violations, Anomalies, Cost Estimate
```

**Uso:** Importar a Excel, Google Sheets, Tableau, etc.

---

## 🔄 Automatización con Cron

Para monitoreo continuo, configura snapshots automáticos:

### Linux/Mac

```bash
# Editar crontab
crontab -e

# Agregar (snapshot cada 5 minutos)
*/5 * * * * cd /path/to/langgraph_agent && python metrics_collector.py snapshot

# Reporte diario a las 9 AM
0 9 * * * cd /path/to/langgraph_agent && python metrics_collector.py report 24 > daily_report.txt
```

### Windows (Task Scheduler)

1. Abrir Task Scheduler
2. Create Basic Task
3. Trigger: Daily / Every 5 minutes
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\metrics_collector.py snapshot`
   - Start in: `C:\path\to\langgraph_agent\`

---

## 📊 Casos de Uso

### 1. Monitoreo en Producción

```bash
# Terminal 1: Dashboard en tiempo real
python dashboard.py

# Terminal 2: Snapshots cada 5 min (mantener corriendo)
while true; do
    python metrics_collector.py snapshot
    sleep 300  # 5 minutos
done
```

Abre el dashboard en el navegador para monitoreo visual.

---

### 2. Análisis Post-Mortem

```bash
# Analizar las últimas 24 horas después de un incidente
python metrics_collector.py report 24

# Detectar qué cambió
python metrics_collector.py trends 24

# Exportar para análisis detallado
python metrics_collector.py export 24 incident_analysis.csv
```

---

### 3. Optimización de Costos

```bash
# Ver proyección mensual
python metrics_collector.py report 168  # 1 semana

# Identificar workflows más costosos
# (Buscar workflows con baja cache hit rate)
```

**Estrategias de optimización:**
- Si cache hit rate <40% → Aumentar TTL del caché
- Si latencia alta en simple → Revisar herramientas
- Si anomalías frecuentes → Ajustar umbrales

---

### 4. Reportes para Management

```bash
# Generar reporte mensual
python metrics_collector.py report 720 > monthly_report.txt

# Exportar para presentación
python metrics_collector.py export 720 monthly_metrics.csv
```

Importa el CSV a Google Sheets/Excel para crear gráficos profesionales.

---

## 🎨 Personalización del Dashboard

### Cambiar Puerto

```python
# En dashboard.py, línea final:
app.run_server(debug=True, host='0.0.0.0', port=8080)  # ← Cambiar aquí
```

### Cambiar Intervalo de Actualización

```python
# En dashboard.py, buscar:
dcc.Interval(
    id='interval-component',
    interval=10*1000,  # ← 10 segundos en vez de 5
    n_intervals=0
)
```

### Agregar Más Gráficos

```python
# Ejemplo: Gráfico de costos
@app.callback(
    Output('cost-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_cost_chart(n):
    # Tu código aquí
    pass
```

---

## 🐛 Troubleshooting

### Dashboard no inicia

**Error:** `ModuleNotFoundError: No module named 'dash'`

**Solución:**
```bash
pip install dash dash-bootstrap-components plotly
```

---

### No se ven datos en el dashboard

**Causa:** No hay archivos de logs generados.

**Solución:**
```bash
# 1. Ejecutar el sistema primero
python orchestrator_v3.py demo

# 2. Verificar que se crearon los logs
ls -la *.jsonl

# Deberías ver:
# router_v2_decisions.jsonl
# orchestrator_v2_metrics.jsonl
# guardrails_violations.jsonl
```

---

### Dashboard muy lento

**Causa:** Demasiados datos en los logs.

**Solución 1:** Limpiar logs antiguos
```bash
# Rotar logs (guardar backup y vaciar)
mv router_v2_decisions.jsonl router_v2_decisions.jsonl.backup
touch router_v2_decisions.jsonl
```

**Solución 2:** Limitar datos cargados
```python
# En dashboard.py, método _load_jsonl:
data = data[-1000:]  # Solo últimas 1000 entradas
```

---

## 📈 Métricas Clave a Monitorear

### 1. **Cache Hit Rate**

| Rango | Interpretación | Acción |
|-------|----------------|--------|
| >60% | ✅ Excelente | Mantener |
| 40-60% | ✅ Bueno | Opcional: aumentar TTL |
| 20-40% | ⚠️  Regular | Revisar TTL y patrones |
| <20% | ❌ Bajo | Aumentar TTL o revisar queries |

### 2. **Latencia Promedio**

| Workflow | Objetivo | Alerta si > |
|----------|----------|-------------|
| Simple | <2s | 3s |
| Sequential | <15s | 25s |
| Agentic | <10s | 20s |
| Conversation | <5s | 10s |

### 3. **Costo por Query**

| Rango | Interpretación |
|-------|----------------|
| <$0.0001 | ✅ Excelente (mucho caché) |
| $0.0001-0.0002 | ✅ Bueno |
| $0.0002-0.0005 | ⚠️  Revisar caché |
| >$0.0005 | ❌ Alto (poco caché o queries complejas) |

---

## 🔗 Integración con Herramientas Externas

### Slack Notifications

```python
# Agregar al metrics_collector.py:
def send_slack_alert(message):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    requests.post(webhook_url, json={"text": message})

# Usar en anomalías críticas:
if critical_anomalies > 5:
    send_slack_alert("🚨 5+ anomalías críticas detectadas!")
```

### Datadog/New Relic

```python
# Enviar métricas a Datadog
from datadog import statsd

statsd.gauge('orchestrator.cache_hit_rate', cache_hit_rate)
statsd.gauge('orchestrator.avg_latency', avg_latency)
```

### Grafana

1. Exportar métricas a CSV periódicamente
2. Importar CSV a base de datos (InfluxDB, Prometheus)
3. Conectar Grafana a la base de datos
4. Crear dashboards personalizados

---

## ✅ Checklist de Setup

- [ ] `dashboard.py` y `metrics_collector.py` copiados
- [ ] Dependencias instaladas (`dash`, `plotly`)
- [ ] Dashboard funciona en `http://localhost:8050`
- [ ] Snapshots se toman correctamente
- [ ] Reportes se generan sin errores
- [ ] (Opcional) Cron job configurado para snapshots automáticos
- [ ] (Opcional) Alertas configuradas

---

## 🎓 Próximos Pasos

1. **Monitorear en Producción:** Dejar el dashboard corriendo
2. **Analizar Tendencias:** Ejecutar `trends` diariamente
3. **Optimizar:** Ajustar TTLs y umbrales basados en datos
4. **Reportes:** Generar reportes semanales para stakeholders

---

**¡Dashboard de Observability listo!** 🎉

Ahora puedes monitorear tu sistema en tiempo real y tomar decisiones basadas en datos. 📊