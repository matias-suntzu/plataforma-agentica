"""Herramientas de acción (modificación de campañas)"""

import logging
from facebook_business.adobjects.adset import AdSet

from ..models.schemas import (
    UpdateAdsetBudgetInput,
    UpdateAdsetBudgetOutput
)

logger = logging.getLogger(__name__)


def update_adset_budget_func(
    input: UpdateAdsetBudgetInput
) -> UpdateAdsetBudgetOutput:
    """🎬 ACCIÓN: Actualiza presupuesto (MOCK)"""
    if isinstance(input, dict):
        adset_id = input.get('adset_id', '')
        new_daily_budget_eur = input.get('new_daily_budget_eur', 0.0)
        reason = input.get('reason', 'No especificada')
    else:
        adset_id = input.adset_id
        new_daily_budget_eur = input.new_daily_budget_eur
        reason = input.reason
    
    # Validación mínimo
    if new_daily_budget_eur < 5.0:
        logger.warning(f"⚠️ Rechazado: {new_daily_budget_eur}€ < 5€")
        return UpdateAdsetBudgetOutput(
            success=False,
            message=f"Presupuesto rechazado: {new_daily_budget_eur}€ < 5€ mínimo",
            adset_id=adset_id,
            new_budget_eur=new_daily_budget_eur
        )
    
    try:
        adset = AdSet(adset_id)
        adset_data = adset.api_get(fields=[AdSet.Field.name, AdSet.Field.daily_budget])
        
        adset_name = adset_data.get(AdSet.Field.name, 'Sin nombre')
        current_budget = adset_data.get(AdSet.Field.daily_budget)
        previous_budget_eur = float(current_budget) / 100 if current_budget else 0.0
        
        budget_change_eur = new_daily_budget_eur - previous_budget_eur
        budget_change_pct = (budget_change_eur / previous_budget_eur * 100) if previous_budget_eur > 0 else 0
        
        # MOCK: No ejecuta cambio real
        logger.info("=" * 60)
        logger.info("🎬 ACCIÓN SIMULADA: Actualización de Presupuesto")
        logger.info(f"📋 Adset: {adset_name} ({adset_id})")
        logger.info(f"💰 Actual: {previous_budget_eur}€ → Nuevo: {new_daily_budget_eur}€")
        logger.info(f"📊 Cambio: {budget_change_eur:+.2f}€ ({budget_change_pct:+.1f}%)")
        logger.info(f"🎯 Razón: {reason}")
        logger.info("⚠️ MOCK: No se ejecutó en Meta Ads API")
        logger.info("=" * 60)
        
        return UpdateAdsetBudgetOutput(
            success=True,
            message=f"✅ SIMULADO: '{adset_name}' de {previous_budget_eur}€ a {new_daily_budget_eur}€ ({budget_change_pct:+.1f}%)",
            adset_id=adset_id,
            previous_budget_eur=previous_budget_eur,
            new_budget_eur=new_daily_budget_eur
        )
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return UpdateAdsetBudgetOutput(
            success=False,
            message=f"Error: {str(e)}",
            adset_id=adset_id,
            new_budget_eur=new_daily_budget_eur
        )
