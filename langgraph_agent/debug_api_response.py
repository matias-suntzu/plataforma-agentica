"""
Script para ver qué está devolviendo el API
"""

import requests
import json

API_URL = "https://plataforma-agentica.onrender.com"  # Tu URL de Render
# O para local: API_URL = "http://localhost:8000"

print("🔍 DEBUGGING API RESPONSE")
print("=" * 70)

# Hacer query simple
response = requests.post(
    f"{API_URL}/query",
    json={
        "query": "lista todas las campañas",
        "user_id": "debug_test"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print("\nRaw Response:")
print(response.text)

print("\n" + "=" * 70)

if response.status_code == 200:
    try:
        data = response.json()
        print("JSON Response (pretty):")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 70)
        print("Keys in response:")
        print(list(data.keys()))
        
        print("\nValues:")
        for key, value in data.items():
            print(f"  {key}: {type(value).__name__} = {str(value)[:100]}...")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
else:
    print(f"❌ Error {response.status_code}")