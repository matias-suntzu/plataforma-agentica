import requests
import json
import time

# URL de PRODUCCIÓN de tu Webhook en n8n
# Esta URL solo funcionará si el workflow está ACTIVO (ON) en n8n
url = "https://matiassuntzu.app.n8n.cloud/webhook/generar-reporte-meta-ads"

# 1. Definir los datos de entrada
# El valor de 'datos_tabla_json' debe ser una cadena JSON, por eso usamos json.dumps()
data = {
    "resumen_ejecutivo": "El anuncio de Baqueira fue el mejor del periodo con 3035 clicks y 80 conversiones, logrando un CPA de €24.79",
    "datos_tabla_json": json.dumps({
        "metadata": {
            "report_title": "Top 3 Anuncios Baqueira",
            "periodo": "last_7d",
            "total_anuncios_analizados": 13
        },
        "data": [{
            "ad_id": "123",
            "ad_name": "Anuncio Baqueira Legacy",
            "clicks": 3035,
            "impressions": 198261,
            "spend": 1983.11,
            "ctr": 1.53,
            "cpm": 10.0,
            "cpc": 0.65,
            "conversiones": 80,
            "cpa": 24.79
        }]
    })
}

print(f"Enviando solicitud POST a: {url}")
start_time = time.time()

try:
    # 2. Enviar la solicitud POST
    # requests convierte automáticamente el diccionario 'data' a JSON en el cuerpo
    response = requests.post(url, json=data)
    
    end_time = time.time()

    # 3. Mostrar resultados
    print("-" * 30)
    print(f"Status Code: {response.status_code}")
    print(f"Tiempo de respuesta: {end_time - start_time:.2f} segundos")
    print("-" * 30)
    
    # Intenta imprimir la respuesta como JSON
    if response.status_code == 200:
        print("Respuesta del Webhook (JSON):")
        print(json.dumps(response.json(), indent=4))
    else:
        print("Error en la respuesta del Webhook:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"Ocurrió un error al conectar: {e}")
