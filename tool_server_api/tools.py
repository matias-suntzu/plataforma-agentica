# /tool_server_api/tools.py

from pydantic import BaseModel, Field # 👈 ¡CAMBIO AQUÍ!
from langchain_core.runnables import RunnableLambda
from typing import Dict, Any, List

# ------------------------------------------------
# 1. Definición de la Interfaz (Pydantic Models)
# ------------------------------------------------

class ListarCampanas(BaseModel):
    """Lista todas las campañas de Meta Ads activas y pausadas en la cuenta."""
    pass 

class BuscarIdCampana(BaseModel):
    """Busca y devuelve el ID de una campaña de Meta Ads por su nombre."""
    nombre_campana: str = Field(description="Nombre completo o parcial de la campaña a buscar.")

class EnviarAlertaSlack(BaseModel):
    """Envía una alerta o un mensaje de reporte urgente al canal de soporte de Slack."""
    mensaje: str = Field(description="El mensaje de alerta o el resumen del reporte a enviar a Slack.")


# ------------------------------------------------
# 2. Lógica de Ejecución (Funciones reales)
# ------------------------------------------------

def listar_campanas_logic(input_data: Dict[str, Any]) -> str:
    """Simula la consulta a Meta Ads."""
    
    # 🚨 Aquí iría la conexión real y autenticada con la API de Meta Ads
    campanas_activas = [
        {"id": "101", "nombre": "Verano 2025", "estado": "ACTIVE"},
        {"id": "102", "nombre": "Back to School", "estado": "PAUSED"},
        {"id": "103", "nombre": "Navidad", "estado": "ACTIVE"},
    ]
    
    return "Campañas encontradas:\n" + "\n".join(
        [f"- {c['nombre']} (ID: {c['id']}, Estado: {c['estado']})" for c in campanas_activas]
    )

def enviar_alerta_slack_logic(input_data: Dict[str, Any]) -> str:
    """Simula el envío de una alerta a Slack."""
    mensaje = input_data.get("mensaje", "Alerta sin mensaje.")
    
    # 🚨 Aquí iría la lógica real para llamar al webhook de Slack
    
    return f"Alerta enviada a Slack exitosamente con el mensaje: '{mensaje}'"


# ------------------------------------------------
# 3. Creación de Runnables (Para LangServe)
# ------------------------------------------------

# Se usan para envolver las funciones y darles el formato de LangChain Runnable
LISTAR_CAMPANAS_RUNNABLE = RunnableLambda(listar_campanas_logic).with_types(
    input_type=ListarCampanas, 
    output_type=str
)

ENVIAR_ALERTA_SLACK_RUNNABLE = RunnableLambda(enviar_alerta_slack_logic).with_types(
    input_type=EnviarAlertaSlack, 
    output_type=str
)

# Lista de todas las herramientas (clases Pydantic) para el LLM
ALL_TOOLS: List[BaseModel] = [ListarCampanas, BuscarIdCampana, EnviarAlertaSlack]

# Diccionario de Runnables para usar en server.py
ALL_RUNNABLES: Dict[str, Any] = {
    "listar_campanas": LISTAR_CAMPANAS_RUNNABLE,
    "enviar_alerta_slack": ENVIAR_ALERTA_SLACK_RUNNABLE
}