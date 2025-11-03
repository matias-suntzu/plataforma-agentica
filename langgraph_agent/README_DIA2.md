# 🚀 DÍA 2: Sequential Workflow + Router Mejorado

## ✅ Entregables del Día 2

Has recibido **4 archivos nuevos**:

1. **`router_v2.py`** - Router mejorado con 4 categorías
2. **`workflows_v2.py`** - Sequential + Conversation Workflows
3. **`orchestrator_v2.py`** - Orchestrator mejorado
4. **`test_day2.py`** - Suite de validación completa

---

## 📁 Estructura del Proyecto (Después del Día 2)

```
langgraph_agent/
├── agent.py                    # ✅ V1 (no modificado)
├── server.py                   # ✅ V1 (no modificado)
│
├── router.py                   # ✅ DÍA 1 (funciona)
├── workflows.py                # ✅ DÍA 1 (funciona)
├── orchestrator.py             # ✅ DÍA 1 (funciona)
├── test_day1.py                # ✅ DÍA 1
│
├── router_v2.py                # 🆕 DÍA 2 - Router mejorado
├── workflows_v2.py             # 🆕 DÍA 2 - Sequential + Conversation
├── orchestrator_v2.py          # 🆕 DÍA 2 - Orchestrator V2
├── test_day2.py                # 🆕 DÍA 2 - Validación
│
├── rag_manager.py              # ✅ Existente
├── memory_manager.py           # ✅ Existente
└── .env                        # ✅ Variables de entorno
```

---

## 🆕 Novedades del Día 2

### 1️⃣ **Router V2: 4 Categorías**

**Antes (Día 1):**
```
- simple
- complejo
```

**Ahora (Día 2):**
```
- simple       ⚡ Listados básicos
- sequential   🔗 Flujos multi-paso (NUEVO)
- agentic      🤖 Análisis complejos
- conversation 💬 Preguntas de seguimiento (NUEVO)
```

**Ejemplo:**
```python
query = "genera un reporte de Baqueira y envíalo a Slack"
router.classify(query)
# → category: "sequential"
# → detected_intent: "report"
# → requires_tools: ["BuscarIdCampanaInput", "GenerarReporteGoogleSlidesInput", "EnviarAlertaSlackInput"]
```

### 2️⃣ **Sequential Workflow**

Ejecuta flujos multi-paso predefinidos:

```
Paso 1: Buscar campaña
   ↓
Paso 2: Obtener métricas
   ↓
Paso 3: Generar reporte (Slides)
   ↓
Paso 4: Enviar a Slack
   ↓
Paso 5: Respuesta final con resumen
```

**Casos de uso:**
- "Genera reporte de X y envíalo a Slack"
- "Analiza campañas activas y crea resumen"
- "Compara períodos y alerta si hay anomalías"

### 3️⃣ **Conversation Workflow**

Maneja preguntas de seguimiento con memoria:

```
Usuario: "TOP 3 de Baqueira"
Agente: [Muestra 3 anuncios]

Usuario: "¿cuál tiene mejor CPA?" ← Conversation Workflow
Agente: [Responde desde memoria, NO re-busca]
```

### 4️⃣ **Logging Estructurado**

Todos los workflows guardan logs en archivos JSONL:

```json
// router_v2_decisions.jsonl
{"timestamp": "2025-10-29T10:30:00", "query": "...", "category": "sequential", "confidence": 0.95}

// orchestrator_v2_metrics.jsonl
{"timestamp": "2025-10-29T10:30:05", "workflow_type": "sequential", "elapsed_time": 12.3}
```

---

## 🚀 Paso a Paso: Implementación del Día 2

### Paso 1: Copiar los Archivos

Copia los 4 nuevos archivos en la raíz de `langgraph_agent/`:

```bash
cd langgraph_agent/
# Copiar router_v2.py, workflows_v2.py, orchestrator_v2.py, test_day2.py
```

### Paso 2: Verificar Configuración

Tu `.env` debe tener (igual que Día 1):

```env
GEMINI_API_KEY=...
TOOL_SERVER_BASE_URL=http://localhost:8000
TOOL_API_KEY=53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG
META_ACCESS_TOKEN=...
META_APP_ID=...
META_APP_SECRET=...
```

**NUEVO (opcional para Sequential Workflow):**
```env
# N8N Webhook para generación de Slides
N8N_SLIDES_WEBHOOK_URL=http://localhost:5678/webhook/generar-reporte-meta-ads

# Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Paso 3: Iniciar Servidor

```bash
cd tool_server_api/
source venv_server/bin/activate
uvicorn server:app --reload --port 8000
```

### Paso 4: Ejecutar Tests

```bash
cd langgraph_agent/
source venv_client/bin/activate
python test_day2.py
```

---

## 📊 Salida Esperada del Test

```
🚀🚀🚀 INICIO DE VALIDACIÓN - DÍA 2 🚀🚀🚀
⏰ Timestamp: 2025-10-29 10:30:00
📍 Validando: Router V2 + Sequential + Conversation Workflows

✅ Variables de entorno configuradas
🔧 Inicializando Orchestrator V2...
✅ Orchestrator V2 inicializado

🔵🔵 TEST 1: PRECISIÓN DEL ROUTER V2 🔵🔵
📝 Query: 'lista todas las campañas'
   Esperado: SIMPLE
✅ PASS
   Obtenido: SIMPLE
   Confidence: 0.95

📝 Query: 'genera un reporte de Baqueira y envíalo a Slack'
   Esperado: SEQUENTIAL
✅ PASS
   Obtenido: SEQUENTIAL
   Confidence: 0.95
   Intent: report

...

📊 RESUMEN DE TESTS:
   Total ejecutados: 12
   ✅ Pasados: 11
   ❌ Fallidos: 1
   📈 Tasa de éxito: 91.7%

🎯 CRITERIOS DE ÉXITO DÍA 2:
   ✅ Router V2 preciso (>85%)
   ✅ Sequential Workflow funcional
   ✅ Conversation usa memoria
   ✅ Backward compatible con V1

🎉 ¡VALIDACIÓN EXITOSA! DÍA 2 COMPLETADO
```

---

## 🎯 Criterios de Éxito del Día 2

| Criterio | Objetivo | Validación |
|----------|----------|------------|
| Router V2 preciso | >85% accuracy | test_day2.py |
| Sequential funciona | 1+ test pasa | test_day2.py |
| Conversation usa memoria | No re-busca datos | test_day2.py |
| Backward compatible | V1 sigue funcionando | test_day2.py |

---

## 🔧 Uso del Orchestrator V2

### Opción 1: Demo Rápido

```bash
python orchestrator_v2.py demo
```

Ejecuta 4 consultas de ejemplo (simple, sequential, agentic, conversation).

### Opción 2: Modo Chat Interactivo

```bash
python orchestrator_v2.py chat
```

**Comandos especiales:**
```
👤 Tú: lista campañas
👤 Tú: metrics          # Ver métricas de rendimiento
👤 Tú: nuevo            # Nuevo thread
👤 Tú: salir            # Terminar (muestra métricas finales)
```

### Opción 3: Uso Programático

```python
from orchestrator_v2 import OrchestratorV2

orchestrator = OrchestratorV2()

# Consulta simple
result = orchestrator.process_query("lista todas las campañas")
print(result.content)

# Consulta sequential
result = orchestrator.process_query(
    "genera un reporte de Baqueira y envíalo a Slack",
    thread_id="user123"
)
print(result.content)

# Ver métricas
orchestrator.print_metrics()
```

---

## 📈 Comparación Día 1 vs Día 2

| Aspecto | Día 1 | Día 2 |
|---------|-------|-------|
| **Categorías Router** | 2 (simple, complejo) | 4 (simple, sequential, agentic, conversation) |
| **Workflows** | 2 (Fast Path, Agentic) | 4 (Fast Path, Sequential, Agentic, Conversation) |
| **Flujos multi-paso** | ❌ No | ✅ Sí (Sequential) |
| **Detección de intención** | ❌ No | ✅ Sí (report, alert, analysis) |
| **Logging estructurado** | ❌ No | ✅ Sí (JSONL files) |
| **Métricas de rendimiento** | ❌ No | ✅ Sí (por workflow) |
| **Backward compatible** | N/A | ✅ Sí (V1 sigue funcionando) |

---

## 🐛 Troubleshooting Día 2

### Error: `ModuleNotFoundError: No module named 'router_v2'`

**Solución:** Verifica que los archivos estén en la raíz de `langgraph_agent/`.

### Error: Sequential Workflow falla en generar Slides

**Causa:** No tienes N8N configurado o el webhook está mal.

**Solución temporal:**
```env
# En tu .env, deja esta línea vacía o comentada
# N8N_SLIDES_WEBHOOK_URL=
```

El Sequential Workflow detectará el error y continuará con Slack.

### Error: Slack no recibe mensajes

**Causa:** `SLACK_WEBHOOK_URL` no configurado o incorrecto.

**Solución:**
1. Crea un Incoming Webhook en Slack
2. Copia la URL en `.env`:
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Test falla en "Conversation usa memoria"

**Causa:** El agente está re-buscando datos en vez de usar memoria.

**Verificación:**
```python
# En test_day2.py, revisa el output:
# ✅ Memoria: Usada
# ⚠️  Memoria: NO usada (re-buscó datos)
```

**Solución:** Verifica que el `thread_id` sea el mismo para todas las consultas de la conversación.

---

## 📝 Ejemplos de Uso Real

### Ejemplo 1: Automatización de Reportes

```python
from orchestrator_v2 import OrchestratorV2
from datetime import datetime

orch = OrchestratorV2()

# Ejecutar diariamente (cron job)
query = f"genera un reporte de campañas activas del {datetime.now().strftime('%Y-%m-%d')} y envíalo a Slack"

result = orch.process_query(query, thread_id=f"daily_report_{datetime.now().date()}")

if "exitosamente" in result.content:
    print("✅ Reporte generado y enviado")
else:
    print(f"❌ Error: {result.content}")
```

### Ejemplo 2: Análisis Interactivo

```python
orch = OrchestratorV2()
thread_id = "analyst_session_001"

# Primera pregunta
result1 = orch.process_query("TOP 5 anuncios de Baqueira", thread_id=thread_id)
print(result1.content)

# Preguntas de seguimiento (usan memoria)
result2 = orch.process_query("¿cuál tiene mejor CPA?", thread_id=thread_id)
print(result2.content)

result3 = orch.process_query("¿y el segundo mejor?", thread_id=thread_id)
print(result3.content)

# Ver métricas
orch.print_metrics()
```

---

## ✅ Checklist de Validación Día 2

Marca cada item:

- [ ] Archivos V2 copiados en la raíz del proyecto
- [ ] `python test_day2.py` ejecuta sin errores críticos
- [ ] Router V2 clasifica >85% correctamente
- [ ] Sequential Workflow detecta patrones multi-paso
- [ ] Conversation Workflow usa memoria (no re-busca)
- [ ] Orchestrator V1 todavía funciona (backward compatible)
- [ ] Logs JSONL se crean correctamente
- [ ] Métricas de rendimiento se muestran con `orchestrator.print_metrics()`

---

## 🎓 Conceptos Clave del Día 2

### 1. Sequential Workflow

**Definición:** Flujo predefinido con pasos en orden específico.

**Ventajas:**
- ⚡ Más rápido que agente puro (pasos predefinidos)
- 🎯 Predecible (siempre mismos pasos)
- 🐛 Fácil debugging (logs por paso)

**Desventajas:**
- ⚠️ Menos flexible que agente
- 🔧 Requiere mantener patrones manualmente

### 2. Conversation Workflow

**Definición:** Workflow optimizado para preguntas de seguimiento.

**Cómo funciona:**
```
1. Usuario: "TOP 3 de Baqueira"
   → Agente busca + analiza + guarda en memoria

2. Usuario: "¿cuál tiene mejor CPA?"
   → Router detecta: CONVERSATION
   → Conversation Workflow usa thread_id
   → Agente recupera mensajes previos
   → Responde SIN llamar herramientas
```

**Beneficio:** Reduce latencia y costos en conversaciones largas.

### 3. Logging Estructurado

**Por qué JSONL:**
- ✅ Una línea = un evento (fácil de parsear)
- ✅ Compatible con herramientas de análisis (jq, pandas)
- ✅ No requiere cerrar/abrir archivos

**Ejemplo de análisis:**
```bash
# Ver todas las consultas "sequential"
grep '"category": "sequential"' router_v2_decisions.jsonl | jq .

# Calcular latencia promedio por workflow
cat orchestrator_v2_metrics.jsonl | jq -s 'group_by(.workflow_type) | map({workflow: .[0].workflow_type, avg_time: (map(.elapsed_time) | add / length)})'
```

---

## 🚀 Próximos Pasos (DÍA 3 - Opcional)

El Día 2 ya cubre lo esencial para producción. Si quieres avanzar al Día 3, agregaremos:

1. **Guardrails avanzados** (validación de datos)
2. **Anomaly detection** (alertas automáticas)
3. **A/B testing de workflows** (experimentación)
4. **Optimización de costos** (caching de resultados)

**Pero NO es necesario para el plan de 3 días original.**

---

**¡Día 2 completado!** 🎉 Ahora tienes un sistema robusto con flujos multi-paso y memoria conversacional. 🚀