import os
from typing import List, Dict, Any, Optional
import logging
from datetime import date, datetime, timedelta 
import requests 
import json 
import io 

from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

from langchain_core.runnables import RunnableLambda
from langserve import add_routes
import uvicorn

from dotenv import load_dotenv
load_dotenv()

# Importaciones de Meta Ads API
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights

# Importaciones de Google APIs y otros
from google.ads.googleads.client import GoogleAdsClient 
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import pandas as pd


# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- 1. Configuración y Inicialización de APIs ---

# 1.1 Meta Ads API
AD_ACCOUNT_ID = os.environ.get('META_AD_ACCOUNT_ID', 'act_952835605437684') 
ACCESS_TOKEN = os.environ.get('META_ACCESS_TOKEN') 
APP_ID = os.environ.get('META_APP_ID')
APP_SECRET = os.environ.get('META_APP_SECRET')

try:
    if not ACCESS_TOKEN or not APP_ID or not APP_SECRET:
        logger.error("❌ Error: Faltan variables de entorno de Meta Ads (META_ACCESS_TOKEN, META_APP_ID, META_APP_SECRET).")
    
    FacebookAdsApi.init(app_id=APP_ID, app_secret=APP_SECRET, access_token=ACCESS_TOKEN)
    account = AdAccount(AD_ACCOUNT_ID)
    logger.info(f"✅ Conexión a Meta Ads API inicializada para la cuenta: {AD_ACCOUNT_ID}")

except Exception as e:
    logger.error(f"❌ Error al inicializar Meta Ads API: {e}")


# 1.2 Google Slides API
# La inicialización se hace dentro de la función por su necesidad de credenciales.
# Solo mostramos un error si faltan las credenciales al inicio.
try:
    # Este archivo debe estar en la carpeta raíz del servidor
    CREDENTIALS_FILE = 'google_slides_credentials.json' 
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error(f"❌ Error al inicializar Google Slides API. Archivo de credenciales '{CREDENTIALS_FILE}' no encontrado.")
except Exception as e:
    logger.error(f"❌ Error desconocido al verificar credenciales de Google Slides: {e}")

# 1.2 Google Slides/Drive API
# CORRECCIÓN: Aseguramos que estas variables existan y tengan valores por defecto si no están en .env
SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', 'google_slides_credentials.json')
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/presentations']
# ID de la plantilla de Google Slides (¡Asegúrate de que esta ID sea correcta!)
TEMPLATE_SLIDES_ID = os.environ.get('TEMPLATE_SLIDES_ID', '1qI2x1b-eYd5F7k-jLp3H-lQ9R8oN7mG-gZ2v4vF5jHl') 
# ID de la carpeta de destino (¡Asegúrate de que esta ID sea correcta!)
DESTINATION_FOLDER_ID = os.environ.get('DESTINATION_FOLDER_ID', '1iK5K_j1nxOFo0zCrxfL-cHJeyZNlJqXj')
SERVICE_ACCOUNT_EMAIL = "agente-marketing-slides@suntzu-475720.iam.gserviceaccount.com" 

# 1.3 Google Ads API
# Inicialización del cliente de Google Ads (se omite por ser solo mock en este ejemplo)


# 1.4 Variables de Google Slides y Slack
SLIDES_TEMPLATE_ID = os.environ.get('SLIDES_TEMPLATE_ID', 'TU_ID_DE_PLANTILLA')
SLIDES_TARGET_FOLDER_ID = os.environ.get('SLIDES_TARGET_FOLDER_ID', 'TU_ID_DE_CARPETA')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', 'TU_URL_DE_WEBHOOK')

# --------------------------------------------------------------------------------
# 🚨 CORRECCIÓN CRÍTICA: DEFINICIÓN Y LIMPIEZA DE LA CLAVE ESPERADA

# Definir la clave API de seguridad que debe coincidir con el agente
TOOL_API_KEY_SERVER = os.environ.get(
    "TOOL_API_KEY", 
    "53b6C9dF-a8Jk0PqR-ZzYxWvUt-42e7H0Lp-Tq8iS1fG" # Clave de fallback
) 

# Limpiar el valor esperado por el servidor para evitar errores de whitespace/comillas
if TOOL_API_KEY_SERVER:
    TOOL_API_KEY_SERVER = TOOL_API_KEY_SERVER.strip().replace('"', '').replace("'", '') 
# --------------------------------------------------------------------------------

# 1.5 Inicialización de FastAPI
app = FastAPI(
    title="Servidor de Herramientas del Agente de Marketing",
    version="1.0",
    description="Servidor LangServe que expone herramientas para Meta Ads, Google Slides y Slack."
)

logger.info("INFO:server:Servidor LangServe inicializado. Herramientas registradas.")


# --- 2. MIDDLEWARE DE AUTENTICACIÓN ---

# Middleware de Autenticación CORREGIDO
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-Tool-Api-Key")
        
        # 🔥 LISTA DE RUTAS PÚBLICAS (sin autenticación)
        public_paths = [
            '/docs',
            '/openapi.json',
            '/redoc',
            '/info',  # ← Agregar esto
            '/health',
            '/favicon.ico'
        ]
        
        # Permitir rutas públicas y playground
        if (request.url.path in public_paths or 
            '/playground/' in request.url.path or 
            '/schema' in request.url.path):
            return await call_next(request)
        
        # Para el resto, verificar API key
        logger.info(f"DEBUG CLAVE: Esperada: '{TOOL_API_KEY_SERVER}' | Recibida: '{api_key}' | Path: {request.url.path}")
        
        if api_key != TOOL_API_KEY_SERVER:
            raise HTTPException(status_code=401, detail="Acceso no autorizado")
        
        response = await call_next(request)
        return response

app.add_middleware(AuthMiddleware)

# --- 3. ESQUEMAS DE DATOS ---

# ... (El resto de tus esquemas de datos como BaseModel permanecen sin cambios)

class ListarCampanasInput(BaseModel):
    placeholder: str = Field(description="Placeholder. Siempre debe ser 'obtener_campanas'.", default="obtener_campanas")
class ListarCampanasOutput(BaseModel):
    campanas_json: str = Field(description="Cadena JSON que contiene la lista de campañas.")

class BuscarIdCampanaInput(BaseModel):
    nombre_campana: str = Field(description="El nombre de la campaña a buscar (ej: 'baqueira').")
class BuscarIdCampanaOutput(BaseModel):
    id_campana: str = Field(description="El ID numérico de la campaña encontrada.")
    nombre_encontrado: str = Field(description="El nombre completo de la campaña tal como se encontró.")

class ObtenerAnunciosPorRendimientoInput(BaseModel):
    campana_id: str = Field(description="El ID numérico de la campaña de Meta Ads.")
    
    # Opción 1: Usar presets
    date_preset: Optional[str] = Field(
        default=None,
        description="El periodo: 'last_month', 'last_7d', etc."
    )
    
    # Opción 2: Usar fechas personalizadas
    date_start: Optional[str] = Field(
        default=None,
        description="Fecha de inicio en formato YYYY-MM-DD (ej: '2025-09-01')"
    )
    date_end: Optional[str] = Field(
        default=None,
        description="Fecha de fin en formato YYYY-MM-DD (ej: '2025-09-30')"
    )
    
    limite: int = Field(default=3, description="Número máximo de anuncios a devolver.")

class ObtenerAnunciosPorRendimientoOutput(BaseModel):
    datos_json: str = Field(description="Cadena JSON con los datos de rendimiento de los anuncios.")

class GenerarReporteGoogleSlidesInput(BaseModel):
    resumen_ejecutivo: str = Field(description="Resumen ejecutivo generado por el LLM sobre los datos de rendimiento.")
    datos_tabla_json: str = Field(description="Tabla de datos JSON con el rendimiento de los anuncios, obtenida del paso anterior.")
class GenerarReporteGoogleSlidesOutput(BaseModel):
    slides_url: str = Field(description="URL de la nueva presentación de Google Slides generada.")

class EnviarAlertaSlackInput(BaseModel):
    mensaje: str = Field(description="El mensaje de alerta a enviar.")
class EnviarAlertaSlackOutput(BaseModel):
    resultado: str = Field(description="Mensaje de confirmación o error del envío a Slack.")

# Esquemas MOCK de Google Ads (mantenerlos aunque no se usen)
class BuscarIdCampanaGoogleInput(BaseModel):
    nombre_campana: str = Field(description="El nombre de la campaña de Google Ads a buscar.")
class BuscarIdCampanaGoogleOutput(BaseModel):
    id_campana: str = Field(description="El ID numérico de la campaña de Google Ads encontrada.")
    nombre_encontrado: str = Field(description="El nombre completo de la campaña tal como se encontró.")

class ObtenerAnunciosPorRendimientoGoogleInput(BaseModel):
    id_campana: str = Field(description="El ID numérico de la campaña de Google Ads.")
    periodo: str = Field(description="El periodo de tiempo para el análisis.")
    limite: int = Field(description="El número máximo de anuncios a devolver.")
class ObtenerAnunciosPorRendimientoGoogleOutput(BaseModel):
    datos_json: str = Field(description="Cadena JSON con los datos de rendimiento de los anuncios.")


# --- 4. FUNCIONES DE HERRAMIENTAS (SIMULADAS O REALES) ---

# ... (El resto de tus funciones como listar_campanas_func, etc., permanecen sin cambios)

# Simulación de Meta Ads: Listar Campañas
def listar_campanas_func(input: ListarCampanasInput) -> ListarCampanasOutput:
    try:
        campanas = account.get_campaigns(fields=['id', 'name', 'status'])
        campanas_data = [{"id": c['id'], "name": c['name'], "status": c.get('status')} for c in campanas]
        
        # Simulación de datos para demostración si la conexión falla o para testing
        if not campanas_data:
            campanas_data = [
                {"id": "120232362248210126", "name": "fbads_es_destino_baqueira_27.08.25", "status": "ACTIVE"},
                {"id": "120232362248210127", "name": "fbads_es_branding_ski_15.09.25", "status": "ACTIVE"},
                {"id": "120232362248210128", "name": "fbads_es_retiro_verano_01.07.26", "status": "PAUSED"},
            ]
        
        return ListarCampanasOutput(campanas_json=json.dumps(campanas_data))
    except Exception as e:
        logger.error(f"Error en listar_campanas_func: {e}")
        # En caso de error, retorna un error simulado para que el LLM lo procese
        return ListarCampanasOutput(campanas_json=json.dumps({"error": f"Error de conexión con Meta Ads: {e}"}))

# Simulación de Meta Ads: Buscar ID Campaña
def buscar_id_campana_func(input: BuscarIdCampanaInput) -> BuscarIdCampanaOutput:
    """
    Busca campaña por nombre O por destino en el adset.
    Ahora soporta búsqueda por destinos como 'Costa Blanca', 'Baqueira', etc.
    """
    # Manejar dict vs objeto Pydantic
    if isinstance(input, dict):
        nombre_buscado = input.get('nombre_campana', '').lower()
    else:
        nombre_buscado = input.nombre_campana.lower()
    
    logger.info(f"Server: Buscando campaña/destino para '{nombre_buscado}'")
    
    # Mapeo de aliases de destinos (para facilitar búsqueda)
    destino_mapping = {
        'baqueira': 'baqueira',
        'ibiza': 'ibiza',
        'menorca': 'menorca',
        'costa del sol': 'costasol',
        'costasol': 'costasol',
        'costa de la luz': 'costaluz',
        'costaluz': 'costaluz',
        'costa blanca': 'costablanca',
        'costablanca': 'costablanca',
        'cantabria': 'cantabria',
        'formentera': 'formentera'
    }
    
    # Normalizar el nombre buscado usando el mapping
    nombre_normalizado = destino_mapping.get(nombre_buscado, nombre_buscado)
    
    try:
        from facebook_business.adobjects.adset import AdSet
        
        # ESTRATEGIA 1: Buscar en nombres de campaña (como antes)
        campaign_fields = [Campaign.Field.name, Campaign.Field.id]
        params = {
            'effective_status': ['ACTIVE', 'PAUSED'],
            'limit': 100
        }
        campaigns = account.get_campaigns(fields=campaign_fields, params=params)
        
        for camp in campaigns:
            camp_name = camp.get(Campaign.Field.name, "").lower()
            
            if nombre_normalizado in camp_name or nombre_buscado in camp_name:
                resultado = BuscarIdCampanaOutput(
                    id_campana=camp.get(Campaign.Field.id),
                    nombre_encontrado=camp.get(Campaign.Field.name)
                )
                logger.info(f"✅ Campaña encontrada (por nombre): {resultado.nombre_encontrado} (ID: {resultado.id_campana})")
                return resultado
        
        # ESTRATEGIA 2: Buscar en nombres de AdSets si no encontró por campaña
        logger.info(f"No encontrado en nombres de campaña, buscando en adsets...")
        
        # Obtener todos los adsets de todas las campañas activas
        for camp in campaigns:
            campaign_id = camp.get(Campaign.Field.id)
            campaign_name = camp.get(Campaign.Field.name)
            
            try:
                # Obtener adsets de esta campaña
                campaign_obj = Campaign(campaign_id)
                adsets = campaign_obj.get_ad_sets(
                    fields=[AdSet.Field.name, AdSet.Field.id],
                    params={'effective_status': ['ACTIVE', 'PAUSED']}
                )
                
                # Buscar el destino en los nombres de adsets
                for adset in adsets:
                    adset_name = adset.get(AdSet.Field.name, "").lower()
                    
                    # Buscar coincidencia con el nombre normalizado
                    if nombre_normalizado in adset_name:
                        resultado = BuscarIdCampanaOutput(
                            id_campana=campaign_id,
                            nombre_encontrado=f"{campaign_name} (destino: {nombre_buscado})"
                        )
                        logger.info(f"✅ Campaña encontrada (por adset): {campaign_name} - AdSet: {adset.get(AdSet.Field.name)}")
                        return resultado
            
            except Exception as e:
                logger.warning(f"Error al buscar en adsets de campaña {campaign_id}: {e}")
                continue
        
        # Si no se encuentra en ningún lado
        logger.warning(f"❌ No se encontró campaña/destino que contenga '{nombre_buscado}'")
        return BuscarIdCampanaOutput(
            id_campana="None",
            nombre_encontrado=f"No se encontró campaña con el nombre o destino '{nombre_buscado}'"
        )
    
    except Exception as e:
        logger.error(f"❌ Error al buscar campaña: {e}")
        return BuscarIdCampanaOutput(
            id_campana="None",
            nombre_encontrado=f"Error al buscar: {str(e)}"
        )

# Simulación de Meta Ads: Obtener Anuncios por Rendimiento
# Meta Ads: Obtener Anuncios por Rendimiento (CON DATOS REALES)
def obtener_anuncios_por_rendimiento_func(input: ObtenerAnunciosPorRendimientoInput) -> ObtenerAnunciosPorRendimientoOutput:
    """
    Obtiene anuncios por rendimiento con soporte para fechas personalizadas.
    """
    # 🔥 DEBUG: Ver qué llega
    logger.info(f"🔥🔥🔥 INPUT RECIBIDO: {input}")
    logger.info(f"🔥🔥🔥 TIPO: {type(input)}")

    # Manejar dict vs objeto Pydantic
    if isinstance(input, dict):
        campana_id = input.get('campana_id', '')
        date_preset = input.get('date_preset')
        date_start = input.get('date_start')
        date_end = input.get('date_end')
        limite = input.get('limite', 3)
    else:
        campana_id = input.campana_id
        date_preset = input.date_preset
        date_start = input.date_start
        date_end = input.date_end
        limite = input.limite
    
    # 🔥 CORRECCIÓN: Priorizar fechas personalizadas sobre preset
    use_custom_range = False
    periodo_str = ""
    
    if date_start and date_end:
        # Si tenemos fechas personalizadas, IGNORAR date_preset
        use_custom_range = True
        periodo_str = f"{date_start} a {date_end}"
        date_preset = None  # ← Anular el preset
    elif date_preset:
        # Usar preset solo si NO hay fechas personalizadas
        use_custom_range = False
        periodo_str = date_preset
    else:
        # Fallback si no hay nada
        date_preset = 'last_7d'
        periodo_str = date_preset
        use_custom_range = False
    
    logger.info(f"Server: Obteniendo anuncios de campaña {campana_id} para el periodo: {periodo_str}")
    
    try:
        campaign = Campaign(campana_id)
        
        insight_fields = [
            AdsInsights.Field.ad_id,
            AdsInsights.Field.ad_name,
            AdsInsights.Field.clicks,
            AdsInsights.Field.impressions,
            AdsInsights.Field.spend,
            AdsInsights.Field.ctr,
            AdsInsights.Field.cpm,
            AdsInsights.Field.cpp,
            AdsInsights.Field.actions,
        ]
        
        # 🔥 CONFIGURAR PARÁMETROS SEGÚN EL TIPO DE FECHA
        if use_custom_range:
            # Usar rango personalizado
            params = {
                'time_range': {
                    'since': date_start,
                    'until': date_end
                },
                'level': 'ad',
            }
            logger.info(f"📅 Usando rango personalizado: {date_start} hasta {date_end}")
        else:
            # Usar preset
            params = {
                'date_preset': date_preset,
                'level': 'ad',
            }
            logger.info(f"📅 Usando preset: {date_preset}")
        
        # Obtener Insights
        ads_insights = campaign.get_insights(
            fields=insight_fields,
            params=params
        )
        
        if not ads_insights:
            logger.warning(f"No se encontraron insights para la campaña {campana_id}")
            return ObtenerAnunciosPorRendimientoOutput(
                datos_json=json.dumps({
                    "error": f"No hay datos de rendimiento para la campaña ID {campana_id} en el periodo {periodo_str}",
                    "sugerencia": "La campaña puede no tener actividad en ese periodo. Prueba con 'últimos 7 días' o verifica las fechas."
                })
            )
        
        # Procesar los resultados
        resultados_procesados = []
        total_spend = 0.0
        total_clicks = 0
        total_impressions = 0
        total_conversions = 0
        
        for insight in ads_insights:
            ad_id = insight.get(AdsInsights.Field.ad_id, 'N/A')
            ad_name = insight.get(AdsInsights.Field.ad_name, 'Sin nombre')
            clicks = int(insight.get(AdsInsights.Field.clicks, 0))
            impressions = int(insight.get(AdsInsights.Field.impressions, 0))
            spend = float(insight.get(AdsInsights.Field.spend, 0.0))
            ctr = float(insight.get(AdsInsights.Field.ctr, 0.0))
            cpm = float(insight.get(AdsInsights.Field.cpm, 0.0))
            
            # Extraer conversiones
            actions = insight.get(AdsInsights.Field.actions, [])
            conversiones = 0
            for action in actions:
                if action.get('action_type') in ['purchase', 'lead', 'complete_registration']:
                    conversiones += int(action.get('value', 0))
            
            # Calcular métricas
            cpc = spend / clicks if clicks > 0 else 0.0
            cpa = spend / conversiones if conversiones > 0 else 0.0
            
            # Acumular totales
            total_spend += spend
            total_clicks += clicks
            total_impressions += impressions
            total_conversions += conversiones
            
            resultados_procesados.append({
                "ad_id": ad_id,
                "ad_name": ad_name,
                "clicks": clicks,
                "impressions": impressions,
                "spend": round(spend, 2),
                "ctr": round(ctr, 2),
                "cpm": round(cpm, 2),
                "cpc": round(cpc, 2),
                "conversiones": conversiones,
                "cpa": round(cpa, 2) if cpa > 0 else 0.0
            })
        
        # Clasificar por clicks
        top_anuncios = sorted(
            resultados_procesados,
            key=lambda x: x['clicks'],
            reverse=True
        )[:limite]
        
        if not top_anuncios:
            logger.warning(f"No se encontraron anuncios con datos en la campaña {campana_id}")
            return ObtenerAnunciosPorRendimientoOutput(
                datos_json=json.dumps({
                    "error": f"No hay anuncios con datos de rendimiento en la campaña ID {campana_id}"
                })
            )
        
        # 🔥 AGREGAR TOTALES DE LA CAMPAÑA
        metadata = {
            "report_title": f"Top {len(top_anuncios)} Anuncios para Campaña ID {campana_id}",
            "periodo": periodo_str,
            "total_anuncios_analizados": len(resultados_procesados),
            "totals": {
                "total_spend": round(total_spend, 2),
                "total_clicks": total_clicks,
                "total_impressions": total_impressions,
                "total_conversions": total_conversions,
                "avg_ctr": round((total_clicks / total_impressions * 100) if total_impressions > 0 else 0, 2),
                "avg_cpc": round(total_spend / total_clicks if total_clicks > 0 else 0, 2)
            }
        }
        
        final_output = {
            "metadata": metadata,
            "data": top_anuncios
        }
        
        logger.info(f"✅ Se obtuvieron {len(top_anuncios)} anuncios. Gasto total: {total_spend:.2f}€")
        return ObtenerAnunciosPorRendimientoOutput(datos_json=json.dumps(final_output))
    
    except Exception as e:
        logger.error(f"❌ Error al obtener anuncios de Meta Ads: {e}", exc_info=True)
        return ObtenerAnunciosPorRendimientoOutput(
            datos_json=json.dumps({
                "error": f"Error al obtener datos de Meta Ads: {str(e)}"
            })
        )

# Google Slides: Generar Reporte (VÍA N8N - TÁCTICA RÁPIDA)
def generar_reporte_google_slides_func(input: GenerarReporteGoogleSlidesInput) -> GenerarReporteGoogleSlidesOutput:
    # Manejar dict vs objeto Pydantic
    if isinstance(input, dict):
        resumen_ejecutivo = input.get('resumen_ejecutivo', '')
        datos_tabla_json = input.get('datos_tabla_json', '')
    else:
        resumen_ejecutivo = input.resumen_ejecutivo
        datos_tabla_json = input.datos_tabla_json
    
    logger.info(f"Generando reporte en Google Slides vía N8N...")
    logger.info(f"Resumen ejecutivo: {resumen_ejecutivo[:100]}...")
    
    # URL del webhook de N8N (actualízala con tu URL real)
    N8N_WEBHOOK_URL = os.getenv('N8N_SLIDES_WEBHOOK_URL', 'http://localhost:5678/webhook/generar-reporte-meta-ads')
    
    try:
        # Validar que los datos JSON sean parseables
        try:
            datos = json.loads(datos_tabla_json)
            logger.info(f"✅ Datos JSON válidos. Anuncios: {len(datos.get('data', []))}")
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear datos_tabla_json: {e}")
            return GenerarReporteGoogleSlidesOutput(
                slides_url=f"Error: No se pudo parsear los datos JSON: {str(e)}"
            )
        
        # Preparar payload para N8N
        payload = {
            "resumen_ejecutivo": resumen_ejecutivo,
            "datos_tabla_json": datos_tabla_json
        }
        
        # Llamar al webhook de N8N
        logger.info(f"📤 Enviando datos a N8N: {N8N_WEBHOOK_URL}")
        
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60  # Timeout de 60 segundos
        )
        
        # Verificar respuesta
        if response.status_code == 200:
            result = response.json()
            presentation_url = result.get('presentation_url')
            
            if presentation_url:
                logger.info(f"✅ Reporte generado exitosamente: {presentation_url}")
                return GenerarReporteGoogleSlidesOutput(slides_url=presentation_url)
            else:
                error_msg = f"❌ N8N respondió OK pero sin URL. Respuesta: {result}"
                logger.error(error_msg)
                return GenerarReporteGoogleSlidesOutput(slides_url=error_msg)
        else:
            error_msg = f"❌ Error de N8N (código {response.status_code}): {response.text}"
            logger.error(error_msg)
            return GenerarReporteGoogleSlidesOutput(slides_url=error_msg)
    
    except requests.exceptions.Timeout:
        error_msg = "❌ Timeout al conectar con N8N (>60s). Verifica que N8N esté corriendo."
        logger.error(error_msg)
        return GenerarReporteGoogleSlidesOutput(slides_url=error_msg)
    
    except requests.exceptions.ConnectionError:
        error_msg = f"❌ No se puede conectar a N8N en {N8N_WEBHOOK_URL}. Verifica que esté corriendo."
        logger.error(error_msg)
        return GenerarReporteGoogleSlidesOutput(slides_url=error_msg)
    
    except Exception as e:
        error_msg = f"❌ Error inesperado al llamar a N8N: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return GenerarReporteGoogleSlidesOutput(slides_url=error_msg)
    
# Herramienta de Slack: Enviar Alerta
def enviar_alerta_slack_func(input: EnviarAlertaSlackInput) -> EnviarAlertaSlackOutput:
    # 🚨 CORRECCIÓN: Manejar dict vs objeto Pydantic
    if isinstance(input, dict):
        mensaje = input.get('mensaje', '')
    else:
        mensaje = input.mensaje
    
    # Si no hay webhook configurado, retornar mensaje informativo
    if not SLACK_WEBHOOK_URL or SLACK_WEBHOOK_URL == 'TU_URL_DE_WEBHOOK':
        logger.warning("⚠️ SLACK_WEBHOOK_URL no configurado. Mensaje no enviado.")
        return EnviarAlertaSlackOutput(
            resultado=f"⚠️ Webhook de Slack no configurado. Mensaje: {mensaje}"
        )
    
    try:
        headers = {'Content-Type': 'application/json'}
        payload = {"text": f"🤖 *Alerta del Agente Meta Ads:*\n{mensaje}"}
        
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            return EnviarAlertaSlackOutput(resultado="✅ Mensaje enviado exitosamente al canal de Slack.")
        else:
            return EnviarAlertaSlackOutput(resultado=f"Error al enviar a Slack. Código: {response.status_code}")

    except Exception as e:
        logger.error(f"Error al enviar a Slack: {e}")
        return EnviarAlertaSlackOutput(resultado=f"Error al enviar a Slack: {e}")


# MOCK: Funciones de Google Ads (mantener mock para el flow del LLM)
def buscar_id_campana_google_func(input: BuscarIdCampanaGoogleInput) -> BuscarIdCampanaGoogleOutput:
    return BuscarIdCampanaGoogleOutput(id_campana="None", nombre_encontrado="No se encontró en Google Ads (MOCK)")

def obtener_anuncios_por_rendimiento_google_func(input: ObtenerAnunciosPorRendimientoGoogleInput) -> ObtenerAnunciosPorRendimientoGoogleOutput:
    return ObtenerAnunciosPorRendimientoGoogleOutput(datos_json=json.dumps({"error": "No implementado (MOCK)"}))

# --- 5. Definición de Chains para LangServe ---

listar_campanas_chain = RunnableLambda(listar_campanas_func).with_types(
    input_type=ListarCampanasInput
)

buscar_id_campana_chain = RunnableLambda(buscar_id_campana_func).with_types(
    input_type=BuscarIdCampanaInput
)

obtener_anuncios_rendimiento_chain = RunnableLambda(obtener_anuncios_por_rendimiento_func).with_types(
    input_type=ObtenerAnunciosPorRendimientoInput
)

enviar_alerta_slack_chain = RunnableLambda(enviar_alerta_slack_func).with_types(
    input_type=EnviarAlertaSlackInput
)

generar_reporte_google_slides_chain = RunnableLambda(generar_reporte_google_slides_func).with_types(
    input_type=GenerarReporteGoogleSlidesInput
)

buscar_id_campana_google_chain = RunnableLambda(buscar_id_campana_google_func).with_types(
    input_type=BuscarIdCampanaGoogleInput
)

obtener_anuncios_rendimiento_google_chain = RunnableLambda(obtener_anuncios_por_rendimiento_google_func).with_types(
    input_type=ObtenerAnunciosPorRendimientoGoogleInput
)


# --- 6. Rutas de LangServe ---\r\n
add_routes(app, listar_campanas_chain, path="/listarcampanas")
add_routes(app, buscar_id_campana_chain, path="/buscaridcampana")
add_routes(app, obtener_anuncios_rendimiento_chain, path="/obteneranunciosrendimiento")
add_routes(app, enviar_alerta_slack_chain, path="/enviaralertaslack")
add_routes(app, generar_reporte_google_slides_chain, path="/generar_reporte_slides")
add_routes(app, buscar_id_campana_google_chain, path="/buscaridcampanagoogle")
add_routes(app, obtener_anuncios_rendimiento_google_chain, path="/obteneranunciosrendimientogoogle")


# --- 7. INICIO DEL SERVIDOR (se usa 'uvicorn server:app') ---
# No se requiere código adicional aquí.