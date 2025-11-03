# test_meta_ads.py

import os
from dotenv import load_dotenv
from server import buscar_id_campana_func, BuscarIdCampana, account

# Cargar variables de entorno
load_dotenv()

print("--- INICIANDO TEST DE BÚSQUEDA ---")

# 1. Verificar conexión a la cuenta
if not account:
    print("❌ ERROR: La variable 'account' de Meta Ads no está inicializada. Revisa .env o server.py.")
    exit()

# 2. Definir el caso de prueba (búsqueda parcial)
NOMBRE_BUSCADO = "baqueira" # El término que el LLM enviaría

# 3. Preparar el input Pydantic
test_input = BuscarIdCampana(nombre_campana=NOMBRE_BUSCADO)

# 4. Ejecutar la función de la herramienta
print(f"Buscando campaña con término: '{NOMBRE_BUSCADO}'...")
test_resultado = buscar_id_campana_func(test_input)

# 5. Imprimir el resultado para depuración
print("\n--- RESULTADO DE LA FUNCIÓN ---")
print(test_resultado)
print("------------------------------")

# 6. Analizar el resultado
if test_resultado.get("id_campana"):
    print(f"✅ ÉXITO: Campaña encontrada. ID: {test_resultado['id_campana']}")
    print(f"Nombre: {test_resultado['nombre_encontrado']}")
    print("El problema está en el LLM (Gemini) que no encadena las llamadas.")
elif test_resultado.get("error"):
    print(f"❌ FALLO DE API: {test_resultado['error']}")
    print("Revisa tus credenciales o permisos de Meta Ads.")
else:
    print(f"⚠️ NO ENCONTRADA: No se halló ninguna campaña que contenga '{NOMBRE_BUSCADO}'.")
    print("Revisa la lista de campañas en tu cuenta de Meta Ads.")

print("--- FIN DEL TEST ---")