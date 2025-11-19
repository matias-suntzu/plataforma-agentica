"""
Schemas de Pydantic para todas las herramientas
Centraliza definiciones para evitar imports circulares
"""

from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField
from typing import Optional


# ========== EXPORTS BASE ==========
# Para que otros módulos usen BaseModel y Field sin importar de pydantic
BaseModel = PydanticBaseModel
Field = PydanticField


# ========== CONFIG SCHEMAS ==========

class ListarCampanasInput(BaseModel):
    """Lista todas las campañas"""
    estado: str = Field(
        default="ACTIVE,PAUSED",
        description="Estados a filtrar: ACTIVE, PAUSED, ARCHIVED"
    )
    limite: int = Field(default=50, description="Máximo de campañas a listar")


class ListarCampanasOutput(BaseModel):
    """Salida con lista de campañas"""
    campanas_json: str


class BuscarCampanaPorNombreInput(BaseModel):
    """Busca campaña por nombre o parte del nombre"""
    nombre_campana: str = Field(description="Nombre o parte del nombre de la campaña")


class BuscarCampanaPorNombreOutput(BaseModel):
    """Salida con ID y nombre de campaña encontrada"""
    id_campana: str
    nombre_encontrado: str


class ObtenerDetallesCampanaInput(BaseModel):
    """Obtiene detalles técnicos completos de una campaña"""
    campana_id: str = Field(description="ID de la campaña")
    incluir_adsets: bool = Field(default=True, description="Incluir detalles de adsets")


class ObtenerDetallesCampanaOutput(BaseModel):
    """Salida con configuración completa"""
    datos_json: str


class ObtenerPresupuestoInput(BaseModel):
    """Obtiene información de presupuesto de una campaña"""
    campana_id: str = Field(description="ID de la campaña")


class ObtenerPresupuestoOutput(BaseModel):
    """Salida con presupuestos"""
    datos_json: str


class ObtenerEstrategiaPujaInput(BaseModel):
    """Obtiene estrategia de puja de una campaña"""
    campana_id: str = Field(description="ID de la campaña")


class ObtenerEstrategiaPujaOutput(BaseModel):
    """Salida con estrategia de puja"""
    datos_json: str


# ========== PERFORMANCE SCHEMAS ==========

class ObtenerMetricasCampanaInput(BaseModel):
    """Obtiene métricas de rendimiento de una campaña"""
    campana_id: str = Field(description="ID de la campaña")
    date_preset: str = Field(default="last_7d", description="Período: last_7d, last_month, etc.")
    date_start: Optional[str] = Field(default=None, description="Fecha inicio personalizada (YYYY-MM-DD)")
    date_end: Optional[str] = Field(default=None, description="Fecha fin personalizada (YYYY-MM-DD)")


class ObtenerMetricasCampanaOutput(BaseModel):
    """Salida con métricas completas"""
    datos_json: str


class ObtenerAnunciosPorRendimientoInput(BaseModel):
    """Obtiene TOP N anuncios de una campaña"""
    campana_id: str = Field(description="ID de la campaña")
    date_preset: str = Field(default="last_7d", description="Período")
    date_start: Optional[str] = Field(default=None, description="Fecha inicio")
    date_end: Optional[str] = Field(default=None, description="Fecha fin")
    limite: int = Field(default=3, description="TOP N anuncios")


class ObtenerAnunciosPorRendimientoOutput(BaseModel):
    """Salida con TOP anuncios"""
    datos_json: str


class CompararPeriodosInput(BaseModel):
    """Compara métricas entre 2 períodos"""
    campana_id: str = Field(description="ID de la campaña (None = todas)")
    periodo_1: str = Field(description="Período 1: 'last_7d', 'this_week', 'custom'")
    periodo_2: str = Field(description="Período 2: 'previous_7d', 'last_week', 'custom'")
    fecha_inicio_1: Optional[str] = Field(default=None, description="Si periodo_1='custom': YYYY-MM-DD")
    fecha_fin_1: Optional[str] = Field(default=None, description="Si periodo_1='custom': YYYY-MM-DD")
    fecha_inicio_2: Optional[str] = Field(default=None, description="Si periodo_2='custom': YYYY-MM-DD")
    fecha_fin_2: Optional[str] = Field(default=None, description="Si periodo_2='custom': YYYY-MM-DD")


class CompararPeriodosOutput(BaseModel):
    """Salida con comparación de períodos"""
    datos_json: str


class ObtenerMetricasGlobalesInput(BaseModel):
    """Obtiene métricas de TODAS las campañas"""
    date_preset: str = Field(default="last_7d", description="Período")


class ObtenerMetricasGlobalesOutput(BaseModel):
    """Salida con métricas globales"""
    datos_json: str


# ========== RECOMMENDATION SCHEMAS ==========
# (Se importarán desde recommendation_tools.py, pero las definimos aquí para evitar imports circulares)

class GetCampaignRecommendationsInput(BaseModel):
    """Obtiene recomendaciones de optimización"""
    campana_id: str = Field(
        default="None",
        description="ID de la campaña (None = todas las activas)"
    )


class GetCampaignRecommendationsOutput(BaseModel):
    """Salida con recomendaciones"""
    datos_json: str


class GetCampaignDetailsInput(BaseModel):
    """Obtiene detalles completos de campaña"""
    campana_id: str = Field(description="ID de la campaña")
    include_adsets: bool = Field(default=True, description="Incluir adsets")


class GetCampaignDetailsOutput(BaseModel):
    """Salida con detalles de campaña"""
    datos_json: str