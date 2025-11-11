"""Modelos Pydantic del servidor"""

from .schemas import (
    ListarCampanasInput, ListarCampanasOutput,
    BuscarIdCampanaInput, BuscarIdCampanaOutput,
    ObtenerAnunciosPorRendimientoInput, ObtenerAnunciosPorRendimientoOutput,
    GetAllCampaignsMetricsInput, GetAllCampaignsMetricsOutput,
    GetCampaignRecommendationsInput, GetCampaignRecommendationsOutput,
    GetCampaignDetailsInput, GetCampaignDetailsOutput,
    UpdateAdsetBudgetInput, UpdateAdsetBudgetOutput,
    GenerarReporteGoogleSlidesInput, GenerarReporteGoogleSlidesOutput,
    EnviarAlertaSlackInput, EnviarAlertaSlackOutput
)

__all__ = [
    'ListarCampanasInput', 'ListarCampanasOutput',
    'BuscarIdCampanaInput', 'BuscarIdCampanaOutput',
    'ObtenerAnunciosPorRendimientoInput', 'ObtenerAnunciosPorRendimientoOutput',
    'GetAllCampaignsMetricsInput', 'GetAllCampaignsMetricsOutput',
    'GetCampaignRecommendationsInput', 'GetCampaignRecommendationsOutput',
    'GetCampaignDetailsInput', 'GetCampaignDetailsOutput',
    'UpdateAdsetBudgetInput', 'UpdateAdsetBudgetOutput',
    'GenerarReporteGoogleSlidesInput', 'GenerarReporteGoogleSlidesOutput',
    'EnviarAlertaSlackInput', 'EnviarAlertaSlackOutput'
]
