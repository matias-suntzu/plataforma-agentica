# 🚀 DÍA 1: Router + Fast Path + Agentic Workflow

## ✅ Entregables

Has recibido **4 archivos nuevos**:

1. **`router.py`** - Clasificador de consultas (Simple vs Complejo)
2. **`workflows.py`** - Fast Path y Agentic Workflows
3. **`orchestrator.py`** - Integración completa
4. **`test_day1.py`** - Script de validación

---

## 📁 Estructura del Proyecto

```
tu_proyecto/
├── agent.py              # ✅ Tu agente actual (NO SE MODIFICA)
├── server.py             # ✅ Tu servidor de herramientas (NO SE MODIFICA)
├── router.py             # 🆕 NUEVO - Clasificador
├── workflows.py          # 🆕 NUEVO - Fast Path + Agentic
├── orchestrator.py       # 🆕 NUEVO - Orquestador principal
├── test_day1.py          # 🆕 NUEVO - Script de validación
├── rag_manager.py        # ✅ Existente
├── memory_manager.py     # ✅ Existente
├── .env                  # ✅ Variables de entorno
└── knowledge_base/       # ✅ RAG y checkpoints
```

---

## 🔧 Paso 1: Instalación de Dependencias

**No necesitas instalar nada nuevo** si ya tienes:
- ✅ `langchain_google_genai`
- ✅ `langgraph`
- ✅ `requests`
- ✅ `pydantic`

Si falta algo:
```bash
pip install langchain-google-genai langgraph requests pydantic
```

---

## 🚀 Paso 2: Verificar Configuración

### 2.1 Variables de Entorno (`.env`)

Verifica que tengas estas variables:

```env
# Gemini API
GEMINI_API_KEY=tu_api_key_aqui

# Tool Server
TOOL_SERVER_BASE_URL=http://localhost:8000
TOOL_API_KEY=53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG

# Meta Ads
META_ACCESS_TOKEN=tu_token_aqui
META_APP_ID=tu_app_id_aqui
META_APP_SECRET=tu_app_secret_aqui
META_AD_ACCOUNT_ID=act_952835605437684

# LangSmith (opcional pero recomendado)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=tu_langsmith_key_aqui
LANGCHAIN_PROJECT=meta-ads-agent
```

### 2.2 Iniciar el Servidor de Herramientas

**En una terminal separada:**

```bash
uvicorn server:app --reload --port 8000
```

Verifica que esté corriendo:
```bash
curl http://localhost:8000/docs
```

Deberías ver la documentación de FastAPI.

---

## 🧪 Paso 3: Ejecutar Tests de Validación

### Opción 1: Test Automático (Recomendado)

```bash
python test_day1.py
```

**Salida esperada:**
```
🚀🚀🚀🚀 INICIO DE VALIDACIÓN - DÍA 1 🚀🚀🚀🚀
⏰ Timestamp: 2025-10-28 10:30:00
📍 Validando: Router + Fast Path + Agentic Workflow

✅ Variables de entorno configuradas
🔧 Inicializando Orchestrator...
✅ Orchestrator inicializado correctamente

🔵🔵 TEST 1: CONSULTAS SIMPLES (FAST PATH) 🔵🔵
...
✅ PASS

🔴🔴 TEST 2: CONSULTAS COMPLEJAS (AGENTIC WORKFLOW) 🔴🔴
...
✅ PASS

📊 RESUMEN DE TESTS:
   Total ejecutados: 6
   ✅ Pasados: 6
   ❌ Fallidos: 0
   📈 Tasa de éxito: 100.0%

🎉 ¡VALIDACIÓN EXITOSA! DÍA 1 COMPLETADO
```

### Opción 2: Demo Rápido

```bash
python orchestrator.py
```

Ejecuta 2 consultas de ejemplo.

### Opción 3: Modo Chat Interactivo

```bash
python orchestrator.py chat
```

Permite probar consultas manualmente:

```
💬 MODO CHAT INTERACTIVO
   Thread ID: interactive_a3f4b9c1
   Comandos: 'salir', 'nuevo'

👤 Tú: lista todas las campañas
🤖 Agente: [respuesta del Fast Path]

👤 Tú: dame el TOP 3 de anuncios de Baqueira
🤖 Agente: [respuesta del Agentic Workflow]
```

---

## 📊 Criterios de Éxito - DÍA 1

Para considerar el Día 1 completado, debes validar:

| Criterio | Cómo Validar |
|----------|--------------|
| ✅ Router funcional | `test_day1.py` clasifica correctamente |
| ✅ Fast Path responde | Consultas simples usan Fast Path |
| ✅ Agentic Workflow responde | Consultas complejas usan Agente |
| ✅ Integración end-to-end | Todos los tests pasan |

**Resultado esperado:**
```
🎯 CRITERIOS DE ÉXITO DÍA 1:
   ✅ Router funcional
   ✅ Fast Path responde
   ✅ Agentic Workflow responde
   ✅ Integración completa
```

---

## 🐛 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'router'`

**Solución:** Asegúrate de que `router.py`, `workflows.py` y `orchestrator.py` estén en el mismo directorio que `agent.py`.

### Error: `Connection refused` al llamar herramientas

**Solución:** Verifica que `server.py` esté corriendo:
```bash
uvicorn server:app --reload --port 8000
```

### Error: `401 Unauthorized` en herramientas

**Solución:** Verifica que `TOOL_API_KEY` en `.env` coincida con el valor en `server.py`:
```
53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG
```

### Fast Path no devuelve campañas

**Solución:** Verifica tus credenciales de Meta Ads en `.env`:
```env
META_ACCESS_TOKEN=...
META_APP_ID=...
META_APP_SECRET=...
```

---

## 🔍 Cómo Funciona (Arquitectura)

```
User Query
    ↓
┌─────────────┐
│   ROUTER    │  → Clasifica en "simple" o "complejo"
└─────────────┘
    ↓
    ├──→ SIMPLE ──→ ┌──────────────────┐
    │               │  FAST PATH       │ → Llama herramienta directamente
    │               │  (sin agente)    │    Respuesta en <1s
    │               └──────────────────┘
    │
    └──→ COMPLEJO ─→ ┌──────────────────┐
                     │ AGENTIC WORKFLOW │ → Usa tu agent.py actual
                     │ (con herramientas)│   Memoria + RAG + Tools
                     └──────────────────┘
```

### Ventajas de esta arquitectura:

1. **Baja latencia:** Consultas simples no pasan por el agente (2-3x más rápido)
2. **Memoria preservada:** El agente sigue usando SqliteSaver
3. **Backward compatible:** Tu `agent.py` actual no se modifica
4. **Escalable:** Fácil agregar nuevos workflows en Día 2 y 3

---

## 📝 Logs de Ejemplo

### Fast Path:
```
⚡ FAST PATH WORKFLOW
   Query: 'lista todas las campañas'
   📡 Llamando a: http://localhost:8000/listarcampanas/invoke
   ✅ Se obtuvieron 15 campañas
```

### Agentic:
```
🤖 AGENTIC WORKFLOW
   Query: 'dame el TOP 3 de anuncios de Baqueira'
   Thread ID: thread_abc123
   ⏳ Ejecutando agente...
   ✅ Respuesta generada
   📊 Herramientas usadas: ['BuscarIdCampanaInput', 'ObtenerAnunciosPorRendimientoInput']
```

---

## ✅ Checklist de Validación

Marca cada item al completarlo:

- [ ] `router.py`, `workflows.py`, `orchestrator.py`, `test_day1.py` copiados al proyecto
- [ ] Variables de entorno configuradas en `.env`
- [ ] `server.py` corriendo en puerto 8000
- [ ] `python test_day1.py` ejecuta sin errores
- [ ] Al menos 5/6 tests pasan (>80% éxito)
- [ ] Fast Path responde en <2 segundos
- [ ] Agentic Workflow usa herramientas correctamente
- [ ] Modo chat interactivo funciona

---

## 🎯 Próximos Pasos (DÍA 2)

Una vez que el Día 1 esté validado, en el Día 2 agregaremos:

1. **Workflow Secuencial** (Tipo 2) para consultas con pasos
2. **Mejoras al Router** (detección de reportes)
3. **Logging estructurado** para debugging

**NO avances al Día 2 hasta validar que todos los tests del Día 1 pasan.**

---

## 💡 Consejos

- **Usa LangSmith:** Facilita el debugging visual de los flujos
- **Prueba manualmente:** El modo chat es excelente para encontrar edge cases
- **Revisa logs:** Los prints con emoji te ayudan a seguir el flujo
- **Thread IDs:** Usa thread IDs consistentes para probar memoria

---

## 🆘 Soporte

Si encuentras errores:

1. Revisa la sección de **Troubleshooting**
2. Verifica los logs en la terminal donde corre `server.py`
3. Usa LangSmith para ver el trace completo
4. Comparte el error específico con el output de `test_day1.py`

---

**¡Éxito con el Día 1!** 🚀