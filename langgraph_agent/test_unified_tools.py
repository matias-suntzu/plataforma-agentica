# test_unified_tools.py
from langgraph_agent.tools import (
    listar_campanas_func,
    get_all_campaigns_metrics_func
)
from langgraph_agent.models.schemas import (
    ListarCampanasInput,
    GetAllCampaignsMetricsInput
)

# Test 1: Listar campañas
print("🧪 Test 1: Listar campañas")
result = listar_campanas_func(ListarCampanasInput())
print(result.campanas_json)

# Test 2: Métricas globales
print("\n🧪 Test 2: Métricas globales")
result = get_all_campaigns_metrics_func(
    GetAllCampaignsMetricsInput(date_preset="last_7d")
)
print(result.datos_json)

print("\n✅ Tests completados")