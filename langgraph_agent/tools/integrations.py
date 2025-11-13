"""Herramientas de integración con servicios externos (Slack, Google Slides)"""

import json
import logging
import requests

from ..models.schemas import (
    GenerarReporteGoogleSlidesInput,
    GenerarReporteGoogleSlidesOutput,
    EnviarAlertaSlackInput,
    EnviarAlertaSlackOutput
)
from ..config.settings import settings

logger = logging.getLogger(__name__)


def generar_reporte_google_slides_func(
    input: GenerarReporteGoogleSlidesInput
) -> GenerarReporteGoogleSlidesOutput:
    """
    Genera reporte de Meta Ads en Google Slides mediante webhook de N8N.
    """
    resumen = input.resumen_ejecutivo if isinstance(input, GenerarReporteGoogleSlidesInput) else input.get('resumen_ejecutivo', '')
    datos = input.datos_tabla_json if isinstance(input, GenerarReporteGoogleSlidesInput) else input.get('datos_tabla_json', '')
    
    # Validar JSON
    try:
        json.loads(datos)
    except json.JSONDecodeError as e:
        return GenerarReporteGoogleSlidesOutput(slides_url=f"Error JSON: {str(e)}")
    
    try:
        response = requests.post(
            settings.N8N_WEBHOOK_URL,
            json={"resumen_ejecutivo": resumen, "datos_tabla_json": datos},
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            url = result.get('presentation_url')
            return GenerarReporteGoogleSlidesOutput(
                slides_url=url if url else f"Error: Sin URL en respuesta"
            )
        else:
            return GenerarReporteGoogleSlidesOutput(
                slides_url=f"Error N8N ({response.status_code}): {response.text}"
            )
    
    except requests.exceptions.Timeout:
        return GenerarReporteGoogleSlidesOutput(slides_url="Error: Timeout (>60s)")
    except requests.exceptions.ConnectionError:
        return GenerarReporteGoogleSlidesOutput(slides_url=f"Error: No conecta a {settings.N8N_WEBHOOK_URL}")
    except Exception as e:
        return GenerarReporteGoogleSlidesOutput(slides_url=f"Error: {str(e)}")


def enviar_alerta_slack_func(
    input: EnviarAlertaSlackInput
) -> EnviarAlertaSlackOutput:
    """
    Envía alerta a Slack mediante webhook.
    """
    mensaje = input.mensaje if isinstance(input, EnviarAlertaSlackInput) else input.get('mensaje', '')
    
    if not settings.SLACK_WEBHOOK_URL or settings.SLACK_WEBHOOK_URL == 'TU_URL_DE_WEBHOOK':
        return EnviarAlertaSlackOutput(resultado=f"⚠️ Webhook no configurado. Mensaje: {mensaje}")
    
    try:
        response = requests.post(
            settings.SLACK_WEBHOOK_URL,
            json={"text": f"🤖 *Alerta Meta Ads:*\n{mensaje}"},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return EnviarAlertaSlackOutput(resultado="✅ Enviado a Slack")
        else:
            return EnviarAlertaSlackOutput(resultado=f"Error {response.status_code}")
    except Exception as e:
        return EnviarAlertaSlackOutput(resultado=f"Error: {str(e)}")