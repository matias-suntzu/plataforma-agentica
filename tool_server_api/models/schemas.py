"""Todos los esquemas Pydantic para las herramientas"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ========== CAMPAÑAS ==========
class ListarCampanasInput(BaseModel):
    placeholder: str = Field(default="obtener_campanas")

class ListarCampanasOutput(BaseModel):
    campanas_json: str


class BuscarIdCampanaInput(BaseModel):
    nombre_campana: str

class BuscarIdCampanaOutput(BaseModel):
    id_campana: str
    nombre_encontrado: str


# ========== ANUNCIOS ==========
class ObtenerAnunciosPorRendimientoInput(BaseModel):
    campana_id: str
    date_preset: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    limite: int = 3

class ObtenerAnunciosPorRendimientoOutput(BaseModel):
    datos_json: str


# ========== MÉTRICAS ==========
class GetAllCampaignsMetricsInput(BaseModel):
    date_preset: str = "last_7d"
    metrics: List[str] = ["spend", "clicks", "ctr", "cpm", "cpc"]

class GetAllCampaignsMetricsOutput(BaseModel):
    datos_json: str


# ========== RECOMENDACIONES ==========
class GetCampaignRecommendationsInput(BaseModel):
    campana_id: Optional[str] = Field(default=None, description="ID campaña (None = todas)")

class GetCampaignRecommendationsOutput(BaseModel):
    datos_json: str


class GetCampaignDetailsInput(BaseModel):
    campana_id: str = Field(description="ID de la campaña")
    include_adsets: bool = Field(default=True, description="Incluir detalles de adsets")

class GetCampaignDetailsOutput(BaseModel):
    datos_json: str


# ========== ACCIONES ==========
class UpdateAdsetBudgetInput(BaseModel):
    adset_id: str = Field(description="ID del adset a actualizar")
    new_daily_budget_eur: float = Field(description="Nuevo presupuesto diario en euros")
    reason: str = Field(description="Razón del cambio (para logging)")

class UpdateAdsetBudgetOutput(BaseModel):
    success: bool
    message: str
    adset_id: str
    previous_budget_eur: Optional[float] = None
    new_budget_eur: float


# ========== INTEGRACIONES ==========
class GenerarReporteGoogleSlidesInput(BaseModel):
    resumen_ejecutivo: str
    datos_tabla_json: str

class GenerarReporteGoogleSlidesOutput(BaseModel):
    slides_url: str


class EnviarAlertaSlackInput(BaseModel):
    mensaje: str

class EnviarAlertaSlackOutput(BaseModel):
    resultado: str