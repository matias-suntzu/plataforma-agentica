# 🚀 Servidor de Herramientas Meta Ads v3.2

Servidor LangServe modular para agente de Meta Ads con arquitectura limpia y mantenible.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Herramientas Disponibles](#-herramientas-disponibles)
- [Testing](#-testing)
- [Integración con Orchestrator](#-integración-con-orchestrator)
- [Migración desde v3.1](#-migración-desde-v31)

---

## ✨ Características

### 🎯 **Funcionalidades Core**
- **9 herramientas** para gestión de campañas Meta Ads
- **Autenticación** mediante API Key
- **Rate limiting** y retry logic para API de Meta
- **Optimización** con recomendaciones automáticas
- **Integraciones** con Slack y Google Slides

### 🏗️ **Arquitectura Modular**
- **85 líneas** en `server.py` (vs 1000+ antes)
- **Separación de responsabilidades** clara
- **Código reutilizable** entre módulos
- **Testing simplificado** por módulo

---

## 🏛️ Arquitectura

```
tool_server_api/
│
├── server.py                    # FastAPI app + rutas (85 líneas)
├── .env                         # Variables de entorno
├── .gitignore
├── requirements.txt
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuración centralizada
│
├── middleware/
│   ├── __init__.py
│   └── auth.py                  # AuthMiddleware (API Key)
│
├── models/
│   ├── __init__.py
│   └── schemas.py               # Pydantic models (Input/Output)
│
├── tools/                       # Lógica de negocio
│   ├── __init__.py
│   ├── campaigns.py             # Listar y buscar campañas
│   ├── ads.py                   # Métricas de anuncios
│   ├── metrics.py               # Métricas globales
│   ├── recommendations.py       # Recomendaciones de optimización
│   ├── actions.py               # Acciones (update budget)
│   └── integrations.py          # Slack, Google Slides
│
├── utils/                       # Utilidades compartidas
│   ├── __init__.py
│   ├── meta_api.py              # Inicialización API de Meta
│   └── helpers.py               # Funciones auxiliares
│
└── test/
    ├── test_v3.1.py             # Tests legacy
    └── test_refactored.py       # Tests modulares ✨
```

---

## 📦 Instalación

### 1️⃣ **Requisitos Previos**
- Python 3.9+
- Cuenta de Meta Ads Developer
- Access Token válido

### 2️⃣ **Clonar y Setup**
```bash
cd tool_server_api/

# Crear estructura de carpetas
mkdir -p config middleware models tools utils

# Crear archivos __init__.py
touch config/__init__.py middleware/__init__.py models/__init__.py tools/__init__.py utils/__init__.py

# Instalar dependencias
pip install -r requirements.txt
```

### 3️⃣ **Copiar Archivos Refactorizados**
Copia los archivos de los artifacts en el orden correcto:

1. `config/settings.py`
2. `middleware/auth.py`
3. `utils/helpers.py`
4. `utils/meta_api.py`
5. `models/schemas.py`
6. `tools/*.py` (todos los archivos de tools/)
7. `server.py`

---

## ⚙️ Configuración

### 1️⃣ **Archivo `.env`**
```bash
# Meta Ads API
META_AD_ACCOUNT_ID=act_XXXXXXXXXXXXX
META_ACCESS_TOKEN=tu_access_token_aqui
META_APP_ID=tu_app_id
META_APP_SECRET=tu_app_secret

# Seguridad
TOOL_API_KEY=tu_api_key_personalizada

# Integraciones (opcional)
N8N_SLIDES_WEBHOOK_URL=http://localhost:5678/webhook/generar-reporte-meta-ads
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 2️⃣ **Validar Configuración**
```python
# En Python REPL o script
from config.settings import settings

# Validar
settings.validate()  # Retorna True si todo está OK
```

---

## 🚀 Uso

### **Iniciar el Servidor**
```bash
# Método 1: Directamente
python server.py

# Método 2: Con Uvicorn (producción)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### **Verificar Estado**
```bash
# Abrir navegador
http://localhost:8000/docs

# O con curl
curl http://localhost:8000/health
```

### **Ejemplo de Request**
```bash
curl -X POST http://localhost:8000/listarcampanas/invoke \
  -H "X-Tool-Api-Key: tu_api_key" \
  -H "Content-Type: application/json" \
  -d '{"input": {"placeholder": "test"}}'
```

---

## 🛠️ Herramientas Disponibles

### 📊 **Consultas (Read-Only)**

| Herramienta | Ruta | Descripción |
|------------|------|-------------|
| **Listar Campañas** | `/listarcampanas` | Lista todas las campañas activas/pausadas |
| **Buscar ID Campaña** | `/buscaridcampana` | Busca campaña por nombre (con mapeo de destinos) |
| **Anuncios por Rendimiento** | `/obteneranunciosrendimiento` | Top N anuncios de una campaña con métricas completas |
| **Métricas Globales** | `/getallcampaignsmetrics` | Métricas agregadas de todas las campañas |
| **Recomendaciones** | `/getcampaignrecommendations` | Sugerencias de optimización basadas en configuración |
| **Detalles de Campaña** | `/getcampaigndetails` | Configuración técnica completa de campaña/adsets |

### 🎬 **Acciones (Write)**

| Herramienta | Ruta | Descripción | Estado |
|------------|------|-------------|--------|
| **Actualizar Presupuesto** | `/updateadsetbudget` | Modifica presupuesto diario de adset | 🟡 MOCK |

### 🔗 **Integraciones**

| Herramienta | Ruta | Descripción |
|------------|------|-------------|
| **Generar Reporte Slides** | `/generar_reporte_slides` | Crea presentación en Google Slides vía N8N |
| **Alerta Slack** | `/enviaralertaslack` | Envía notificación a canal de Slack |

---

## 🧪 Testing

### **Test Completo (Recomendado)**
```bash
python test/test_refactored.py
```

**Salida esperada:**
```
🧪 TESTS DE REFACTORIZACIÓN - Servidor Meta Ads v3.2
======================================================================

📁 FASE 1: Verificando estructura de archivos...
   ✅ Existe: config/__init__.py
   ✅ Existe: config/settings.py
   ...
   ✅ ÉXITO: Todos los archivos existen (16 archivos)

📦 FASE 2: Verificando imports de módulos...
   ✅ config.settings.settings
   ✅ middleware.auth.AuthMiddleware
   ...
   ✅ ÉXITO: Todos los imports funcionan (11 módulos)

...

📊 RESUMEN DE TESTS
======================================================================
   ✅ PASÓ: Estructura de Archivos
   ✅ PASÓ: Imports de Módulos
   ✅ PASÓ: Configuración
   ✅ PASÓ: Funciones Auxiliares
   ✅ PASÓ: Esquemas Pydantic
   ✅ PASÓ: Servidor FastAPI
   ✅ PASÓ: Integración

======================================================================
🎯 RESULTADO FINAL: 7/7 tests pasaron
======================================================================

🎉 ¡REFACTORIZACIÓN EXITOSA! Todos los tests pasaron.
```

### **Tests Individuales**
```bash
# Test de estructura
python test/test_refactored.py structure

# Test de imports
python test/test_refactored.py imports

# Test de helpers
python test/test_refactored.py helpers
```

### **Tests Legacy (v3.1)**
```bash
python test/test_v3.1.py
```

---

## 🔄 Integración con Orchestrator

### **Uso desde `orchestrator_v3.py`**

El orchestrator **NO requiere cambios** porque:
- ✅ Las rutas HTTP son idénticas
- ✅ El formato de request/response no cambia
- ✅ La autenticación sigue siendo la misma

**Pero ahora puedes reutilizar código:**

```python
# En langgraph_agent/orchestrator_v3.py (opcional)

# Reutilizar helpers
from tool_server_api.utils.helpers import safe_int_from_insight

# Reutilizar configuración
from tool_server_api.config.settings import settings

# Ejemplo: Validar configuración al inicio
if not settings.validate():
    raise ValueError("Configuración inválida")
```

### **Variables de Entorno Compartidas**

Ambos proyectos pueden usar el mismo `.env`:

```bash
# En la raíz del proyecto
agente-meta-mcp-personal/.env  # Configuración global

# Symlink (opcional)
cd tool_server_api/
ln -s ../.env .env
```

---

## 🔄 Migración desde v3.1

### **¿Qué cambió?**

| Aspecto | v3.1 (Antes) | v3.2 (Ahora) |
|---------|--------------|--------------|
| **Estructura** | 1 archivo monolítico | 16 archivos modulares |
| **server.py** | 1000+ líneas | 85 líneas |
| **Mantenibilidad** | Difícil | Excelente |
| **Testing** | Complejo | Simple |
| **Imports** | Todo en `server.py` | Módulos independientes |

### **¿Qué NO cambió?**

- ✅ Rutas HTTP (`/listarcampanas`, etc.)
- ✅ Formato de request/response
- ✅ Autenticación (X-Tool-Api-Key)
- ✅ Lógica de negocio (funciones idénticas)
- ✅ Variables de entorno

### **Pasos de Migración**

1. **Backup del server.py original**
   ```bash
   cp server.py server_v3.1_backup.py
   ```

2. **Crear estructura modular**
   ```bash
   mkdir -p config middleware models tools utils
   ```

3. **Copiar archivos refactorizados**
   (Ver sección de Instalación)

4. **Ejecutar tests**
   ```bash
   python test/test_refactored.py
   ```

5. **Comparar comportamiento**
   ```bash
   # Terminal 1: Servidor refactorizado
   python server.py

   # Terminal 2: Tests
   python test/test_v3.1.py
   ```

6. **Si todo funciona, eliminar backup**
   ```bash
   rm server_v3.1_backup.py
   ```

---

## 📝 Notas Adicionales

### **⚠️ Modo MOCK para Acciones**

La herramienta `update_adset_budget` está en **modo MOCK** por seguridad:
- ✅ Valida input
- ✅ Obtiene datos actuales
- ✅ Calcula cambios
- ❌ **NO ejecuta** cambios reales en Meta Ads

Para **activar modo real**:
```python
# En tools/actions.py, descomentar:
# adset.api_update(params={'daily_budget': new_budget_cents})
```

### **🔐 Seguridad**

- Todas las rutas (excepto `/docs`) requieren `X-Tool-Api-Key`
- Cambiar `TOOL_API_KEY` en `.env` para producción
- No commitear `.env` al repositorio (ya está en `.gitignore`)

### **📊 Logging**

```python
# Configurar nivel de logging
import logging
logging.basicConfig(level=logging.DEBUG)  # Ver todo
```

---

## 🆘 Troubleshooting

### **Error: "Module not found"**
```bash
# Verificar que estás en el directorio correcto
pwd  # Debe ser tool_server_api/

# Verificar __init__.py
ls -la config/__init__.py
```

### **Error: "ACCESS_TOKEN no configurado"**
```bash
# Verificar .env
cat .env | grep META_ACCESS_TOKEN

# Validar configuración
python -c "from config.settings import settings; settings.validate()"
```

### **Error: "Falta archivo X"**
```bash
# Ejecutar tests para identificar qué falta
python test/test_refactored.py structure
```

---

## 📚 Recursos

- **Documentación Meta Ads API**: https://developers.facebook.com/docs/marketing-api
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **LangServe**: https://github.com/langchain-ai/langserve
- **Pydantic**: https://docs.pydantic.dev

---

## 🤝 Contribuir

Para agregar nuevas herramientas:

1. **Crear función en `tools/`**
   ```python
   # tools/nueva_herramienta.py
   def mi_nueva_herramienta_func(input):
       # Lógica aquí
       return output
   ```

2. **Definir schemas en `models/schemas.py`**
   ```python
   class MiNuevaHerramientaInput(BaseModel):
       param1: str
   ```

3. **Registrar en `server.py`**
   ```python
   chains['/minuevaherramienta'] = RunnableLambda(mi_nueva_herramienta_func)
   ```

4. **Agregar tests en `test/test_refactored.py`**

---

## 📄 Licencia

Este proyecto es parte del sistema de agentes de Meta Ads.

---

## 📞 Contacto

Para dudas o sugerencias, contactar al equipo de desarrollo.

---

**Versión**: 3.2 (Refactorizado)  
**Última actualización**: Noviembre 2025  
**Estado**: ✅ Producción