"""Herramienta simulada para actualizar presupuesto (modo sandbox)"""

import json
import time
import logging
from ..models.schemas import UpdateBudgetInput, UpdateBudgetOutput

logger = logging.getLogger(__name__)

def update_budget_func(input: UpdateBudgetInput) -> UpdateBudgetOutput:
    """
    Simula la actualización de presupuesto de un AdSet en Meta Ads (sin modificar datos reales).
    Ideal para pruebas E2E de conectividad.
    """
    try:
        adset_id = input.adset_id
        new_budget = input.new_budget

        # Validaciones básicas
        if not adset_id or not str(adset_id).isdigit():
            return UpdateBudgetOutput(success=False, message="AdSet ID inválido o vacío.")

        if new_budget <= 0:
            return UpdateBudgetOutput(success=False, message="El presupuesto debe ser mayor que 0.")

        # Simular latencia y resultado exitoso
        logger.info(f"🔧 Simulando actualización de presupuesto para AdSet {adset_id} → {new_budget}")
        time.sleep(1.5)  # Simula tiempo de red/API
        response = {
            "adset_id": adset_id,
            "new_budget": new_budget,
            "status": "ok",
            "sandbox": True
        }

        return UpdateBudgetOutput(success=True, message=json.dumps(response))

    except Exception as e:
        logger.error(f"Error en simulación UpdateBudget: {e}", exc_info=True)
        return UpdateBudgetOutput(success=False, message=str(e))
