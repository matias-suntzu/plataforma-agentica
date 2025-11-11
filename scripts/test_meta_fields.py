# test_meta_fields.py
import os
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adsinsights import AdsInsights

load_dotenv()

FacebookAdsApi.init(
    app_id=os.getenv('META_APP_ID'),
    app_secret=os.getenv('META_APP_SECRET'),
    access_token=os.getenv('META_ACCESS_TOKEN')
)

print("📊 CAMPOS DISPONIBLES EN AdsInsights:\n")

# Obtener todos los campos
all_fields = dir(AdsInsights.Field)
insight_fields = [f for f in all_fields if not f.startswith('_')]

# Categorizar por tipo
metrics = {}
for field in sorted(insight_fields):
    value = getattr(AdsInsights.Field, field)
    
    # Categorizar
    if any(x in field.lower() for x in ['cost', 'cpa', 'cpc', 'cpm', 'cpp']):
        category = "💰 Costos"
    elif any(x in field.lower() for x in ['click', 'ctr']):
        category = "🖱️ Clicks"
    elif any(x in field.lower() for x in ['impression', 'reach', 'frequency']):
        category = "👁️ Alcance"
    elif any(x in field.lower() for x in ['conversion', 'purchase', 'action']):
        category = "🎯 Conversiones"
    elif any(x in field.lower() for x in ['video', 'watch']):
        category = "🎥 Video"
    elif any(x in field.lower() for x in ['spend', 'budget']):
        category = "💵 Presupuesto"
    else:
        category = "📋 Otros"
    
    if category not in metrics:
        metrics[category] = []
    
    metrics[category].append(f"  • {field} = '{value}'")

# Imprimir por categoría
for category, fields in sorted(metrics.items()):
    print(f"\n{category}:")
    for field in fields[:20]:  # Limitar a 20 por categoría
        print(field)

print(f"\n✅ Total de campos disponibles: {len(insight_fields)}")