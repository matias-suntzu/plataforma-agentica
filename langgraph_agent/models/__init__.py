"""
Modelos y schemas Pydantic
"""

from .schemas import (
    # Inputs de herramientas
    ListarCampanasInput,
    BuscarIdCampanaInput,
    ObtenerAnunciosPorRendimientoInput,
    GetAllCampaignsMetricsInput,
    GetCampaignRecommendationsInput,
    GetCampaignDetailsInput,
    UpdateAdsetBudgetInput,
    EnviarAlertaSlackInput,
    GenerarReporteGoogleSlidesInput,
    
    # Outputs de herramientas
    ListarCampanasOutput,
    BuscarIdCampanaOutput,
    ObtenerAnunciosPorRendimientoOutput,
    GetAllCampaignsMetricsOutput,
    GetCampaignRecommendationsOutput,
    GetCampaignDetailsOutput,
    UpdateAdsetBudgetOutput,
)

__all__ = [
    # Inputs
    'ListarCampanasInput',
    'BuscarIdCampanaInput',
    'ObtenerAnunciosPorRendimientoInput',
    'GetAllCampaignsMetricsInput',
    'GetCampaignRecommendationsInput',
    'GetCampaignDetailsInput',
    'UpdateAdsetBudgetInput',
    'EnviarAlertaSlackInput',
    'GenerarReporteGoogleSlidesInput',
    
    # Outputs
    'ListarCampanasOutput',
    'BuscarIdCampanaOutput',
    'ObtenerAnunciosPorRendimientoOutput',
    'GetAllCampaignsMetricsOutput',
    'GetCampaignRecommendationsOutput',
    'GetCampaignDetailsOutput',
    'UpdateAdsetBudgetOutput',
]