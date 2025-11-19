"""
Models Package
Exports para schemas y modelos de datos
"""

from .schemas import (
    BaseModel,
    Field,
    # Config Schemas
    ListarCampanasInput,
    ListarCampanasOutput,
    BuscarCampanaPorNombreInput,
    BuscarCampanaPorNombreOutput,
    ObtenerDetallesCampanaInput,
    ObtenerDetallesCampanaOutput,
    ObtenerPresupuestoInput,
    ObtenerPresupuestoOutput,
    ObtenerEstrategiaPujaInput,
    ObtenerEstrategiaPujaOutput,
    # Performance Schemas
    ObtenerMetricasCampanaInput,
    ObtenerMetricasCampanaOutput,
    ObtenerAnunciosPorRendimientoInput,
    ObtenerAnunciosPorRendimientoOutput,
    CompararPeriodosInput,
    CompararPeriodosOutput,
    ObtenerMetricasGlobalesInput,
    ObtenerMetricasGlobalesOutput,
)

__all__ = [
    "BaseModel",
    "Field",
    # Config
    "ListarCampanasInput",
    "ListarCampanasOutput",
    "BuscarCampanaPorNombreInput",
    "BuscarCampanaPorNombreOutput",
    "ObtenerDetallesCampanaInput",
    "ObtenerDetallesCampanaOutput",
    "ObtenerPresupuestoInput",
    "ObtenerPresupuestoOutput",
    "ObtenerEstrategiaPujaInput",
    "ObtenerEstrategiaPujaOutput",
    # Performance
    "ObtenerMetricasCampanaInput",
    "ObtenerMetricasCampanaOutput",
    "ObtenerAnunciosPorRendimientoInput",
    "ObtenerAnunciosPorRendimientoOutput",
    "CompararPeriodosInput",
    "CompararPeriodosOutput",
    "ObtenerMetricasGlobalesInput",
    "ObtenerMetricasGlobalesOutput",
]