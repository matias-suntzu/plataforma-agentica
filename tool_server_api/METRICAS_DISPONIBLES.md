# 📊 Métricas Disponibles - Meta Ads API

## 🎯 Métricas Implementadas en V3.1

### ✅ Métricas Básicas
| Campo API | Nombre | Descripción |
|-----------|---------|-------------|
| `spend` | Gasto | Gasto total en euros |
| `impressions` | Impresiones | Número de veces que se mostró el anuncio |
| `clicks` | Clics | Clics totales en el anuncio |
| `ctr` | CTR | Click-through rate (%) |
| `cpm` | CPM | Costo por mil impresiones |
| `cpc` | CPC | Costo por clic |

### ✅ Alcance y Frecuencia
| Campo API | Nombre | Descripción |
|-----------|---------|-------------|
| `reach` | Alcance | Personas únicas alcanzadas |
| `frequency` | Frecuencia | Promedio de veces que cada persona vio el anuncio |

### ✅ Clics Avanzados
| Campo API | Nombre | Descripción |
|-----------|---------|-------------|
| `inline_link_clicks` | Clics en enlace | Clics en enlaces dentro del anuncio |
| `inline_link_click_ctr` | CTR de enlace | CTR específico de enlaces |
| `outbound_clicks` | Clics salientes | Clics que llevan fuera de Facebook |
| `outbound_clicks_ctr` | CTR saliente | CTR de clics salientes |

### ✅ Costos por Acción
| Campo API | Nombre | Descripción |
|-----------|---------|-------------|
| `cost_per_inline_link_click` | Costo/clic enlace | Costo por clic en enlace |
| `cost_per_outbound_click` | Costo/clic saliente | Costo por clic saliente |
| `cost_per_unique_click` | Costo/clic único | Costo por clic único |
| `cost_per_conversion` | Costo/conversión | Costo por conversión |

### ✅ Conversiones
| Campo API | Nombre | Descripción |
|-----------|---------|-------------|
| `conversions` | Conversiones | Total de conversiones |
| `conversion_values` | Valor de conversiones | Valor monetario de conversiones |
| `actions` | Acciones | Array de acciones (purchase, lead, etc.) |

---

## 🔜 Métricas Disponibles NO Implementadas

### 🎥 Métricas de Video (Pendientes)
```python
# Agregar a insight_fields en obtener_anuncios_por_rendimiento_func()

AdsInsights.Field.unique_video_view_15_sec,  # Reproducciones únicas de 15s
AdsInsights.Field.video_view_per_impression,  # Reproducciones por impresión
```

**Casos de uso:**
- Analizar rendimiento de anuncios en video
- Optimizar creativos de video
- Calcular engagement de video

---

### 💰 Costos Adicionales (Pendientes)
```python
AdsInsights.Field.cost_per_15_sec_video_view,      # Costo por 15s de video
AdsInsights.Field.cost_per_2_sec_continuous_video_view,  # Costo por 2s de video
AdsInsights.Field.cost_per_thruplay,               # Costo por reproducción completa
AdsInsights.Field.cost_per_estimated_ad_recallers, # Costo por recuerdo estimado
```

**Casos de uso:**
- Optimización de presupuesto en campañas de video
- Análisis de eficiencia de recordación

---

### 🎯 Conversiones Avanzadas (Pendientes)
```python
AdsInsights.Field.conversion_rate_ranking,  # Ranking de tasa de conversión
AdsInsights.Field.conversion_lead_rate,     # Tasa de conversión a lead
AdsInsights.Field.conversion_leads,         # Leads totales

# ROAS (Return on Ad Spend)
AdsInsights.Field.catalog_segment_value_website_purchase_roas,
AdsInsights.Field.catalog_segment_value_mobile_purchase_roas,
AdsInsights.Field.catalog_segment_value_omni_purchase_roas,

# Compras por canal
AdsInsights.Field.converted_product_website_pixel_purchase,
AdsInsights.Field.converted_product_app_custom_event_fb_mobile_purchase,
AdsInsights.Field.converted_product_omni_purchase,
AdsInsights.Field.converted_product_offline_purchase,
```

**Casos de uso:**
- Análisis de ROAS por canal (web, mobile, omni)
- Optimización de campañas de e-commerce
- Análisis de atribución multicanal

---

### 👁️ Alcance Avanzado (Pendientes)
```python
AdsInsights.Field.full_view_impressions,  # Impresiones vistas completamente
AdsInsights.Field.full_view_reach,        # Alcance de vistas completas
AdsInsights.Field.ad_impression_actions,  # Acciones por impresión
```

**Casos de uso:**
- Análisis de visibilidad real de anuncios
- Optimización de creativos para máxima visibilidad

---

### 🖱️ Clics Avanzados (Pendientes)
```python
AdsInsights.Field.ad_click_actions,  # Acciones después de clic
AdsInsights.Field.instant_experience_clicks_to_open,    # Clics en Instant Experience
AdsInsights.Field.instant_experience_clicks_to_start,   # Inicios de Instant Experience
AdsInsights.Field.instant_experience_outbound_clicks,   # Clics salientes desde IE

# Landing Page
AdsInsights.Field.landing_page_view_actions_per_link_click,  # Acciones por vista de LP
AdsInsights.Field.landing_page_view_per_link_click,          # Vistas de LP por clic

# Relaciones
AdsInsights.Field.link_clicks_per_results,        # Clics por resultado
AdsInsights.Field.purchases_per_link_click,       # Compras por clic
```

**Casos de uso:**
- Análisis de journey del usuario
- Optimización de landing pages
- Medición de eficiencia de conversión

---

### 📋 Contexto de Campaña (Pendientes)
```python
AdsInsights.Field.campaign_name,     # Nombre de campaña
AdsInsights.Field.campaign_id,       # ID de campaña
AdsInsights.Field.adset_name,        # Nombre de adset
AdsInsights.Field.adset_id,          # ID de adset
AdsInsights.Field.adset_start,       # Fecha inicio adset
AdsInsights.Field.adset_end,         # Fecha fin adset
AdsInsights.Field.age_targeting,     # Targeting de edad
AdsInsights.Field.buying_type,       # Tipo de compra (AUCTION, RESERVED)
AdsInsights.Field.objective,         # Objetivo de campaña
```

**Casos de uso:**
- Reportes consolidados con contexto
- Análisis de targeting efectivo

---

### 💵 Presupuesto y Gasto Social (Pendientes)
```python
AdsInsights.Field.social_spend,  # Gasto en acciones sociales
AdsInsights.Field.marketing_messages_spend,  # Gasto en mensajes marketing
AdsInsights.Field.marketing_messages_spend_currency,  # Moneda de gasto
```

**Casos de uso:**
- Análisis de gasto por tipo de acción
- Desglose de presupuesto

---

### 🏆 Ranking y Competitividad (Pendientes)
```python
AdsInsights.Field.auction_competitiveness,      # Competitividad en subasta
AdsInsights.Field.auction_max_competitor_bid,   # Puja máxima del competidor
AdsInsights.Field.auction_bid,                  # Puja real
AdsInsights.Field.conversion_rate_ranking,      # Ranking de tasa de conversión
```

**Casos de uso:**
- Análisis de competencia
- Optimización de estrategia de puja
- Benchmarking

---

## 📝 Cómo Agregar Nuevas Métricas

### Paso 1: Agregar al `insight_fields`
```python
# En server.py > obtener_anuncios_por_rendimiento_func()

insight_fields = [
    # ... campos existentes ...
    
    # 🆕 Agregar nuevos campos
    AdsInsights.Field.unique_video_view_15_sec,
    AdsInsights.Field.cost_per_15_sec_video_view,
    # ...
]
```

### Paso 2: Extraer y Procesar
```python
# Dentro del loop for insight in ads_insights:

# 🆕 Video metrics
video_views_15s = int(insight.get(AdsInsights.Field.unique_video_view_15_sec, 0))
cost_per_video_view = float(insight.get(AdsInsights.Field.cost_per_15_sec_video_view, 0.0))
```

### Paso 3: Agregar a Resultados
```python
resultados.append({
    # ... campos existentes ...
    
    # 🆕 Nuevos campos
    "video_views_15s": video_views_15s,
    "cost_per_video_view": round(cost_per_video_view, 2),
})
```

### Paso 4: Actualizar Totales (si aplica)
```python
totals = {
    # ... existentes ...
    'total_video_views': 0,  # 🆕
}

# En el loop:
totals['total_video_views'] += video_views_15s
```

### Paso 5: Actualizar Documentación
- Actualizar `README_V3.1.md`
- Actualizar `agent.py` (section 8 de SYSTEM_INSTRUCTION)
- Agregar casos de prueba en `test_v3.1.py`

---

## 🎯 Priorización de Implementación

### 🔴 Alta Prioridad
1. **Métricas de Video** (para campañas con contenido audiovisual)
   - `unique_video_view_15_sec`
   - `cost_per_15_sec_video_view`
   
2. **ROAS** (para e-commerce)
   - `catalog_segment_value_website_purchase_roas`
   - `catalog_segment_value_mobile_purchase_roas`

3. **Contexto de Campaña** (para reportes completos)
   - `campaign_name`
   - `adset_name`
   - `objective`

### 🟡 Media Prioridad
4. **Clics Avanzados** (para análisis de journey)
   - `landing_page_view_per_link_click`
   - `purchases_per_link_click`

5. **Ranking y Competitividad** (para optimización)
   - `auction_competitiveness`
   - `conversion_rate_ranking`

### 🟢 Baja Prioridad
6. **Instant Experience** (si se usa este formato)
   - `instant_experience_clicks_to_open`
   - `instant_experience_outbound_clicks`

7. **Marketing Messages** (si se usa WhatsApp/Messenger)
   - `marketing_messages_spend`
   - `marketing_messages_link_btn_click_rate`

---

## 🧪 Testing de Nuevas Métricas

```python
# test_new_metrics.py

import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

LANGSERVE_URL = os.getenv("TOOL_SERVER_BASE_URL", "http://localhost:8000")
TOOL_API_KEY = os.getenv("TOOL_API_KEY")

def test_new_metrics():
    """Prueba las nuevas métricas agregadas"""
    
    # 1. Buscar campaña
    response = requests.post(
        f"{LANGSERVE_URL}/buscaridcampana/invoke",
        headers={"X-Tool-Api-Key": TOOL_API_KEY},
        json={"input": {"nombre_campana": "baqueira"}}
    )
    
    campaign_id = response.json()['output']['id_campana']
    
    # 2. Obtener anuncios con nuevas métricas
    response = requests.post(
        f"{LANGSERVE_URL}/obteneranunciosrendimiento/invoke",
        headers={"X-Tool-Api-Key": TOOL_API_KEY},
        json={"input": {
            "campana_id": campaign_id,
            "date_preset": "last_7d",
            "limite": 3
        }}
    )
    
    result = json.loads(response.json()['output']['datos_json'])
    
    # 3. Verificar que las nuevas métricas existen
    for ad in result['data']:
        assert 'reach' in ad, "Falta métrica: reach"
        assert 'inline_link_clicks' in ad, "Falta métrica: inline_link_clicks"
        assert 'cost_per_conversion' in ad, "Falta métrica: cost_per_conversion"
        
        print(f"✅ Anuncio {ad['ad_name']}:")
        print(f"   Reach: {ad['reach']}")
        print(f"   Inline Link Clicks: {ad['inline_link_clicks']}")
        print(f"   Cost per Conversion: {ad['cost_per_conversion']}€")

if __name__ == "__main__":
    test_new_metrics()
```

---

## 📚 Referencias

- [Meta Ads Insights API](https://developers.facebook.com/docs/marketing-api/insights)
- [AdsInsights Fields Reference](https://developers.facebook.com/docs/marketing-api/insights/fields)
- [Best Practices for Metrics](https://www.facebook.com/business/help/735598939869927)

---

**Última actualización:** 2025-01-XX  
**Versión:** 3.1  
**Total métricas implementadas:** 22  
**Total métricas disponibles:** 193