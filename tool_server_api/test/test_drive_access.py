import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURACIÓN ---
# 1. Asegúrate de que este archivo exista en tu carpeta.
SERVICE_ACCOUNT_FILE = 'google_slides_credentials.json' 
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_EMAIL = 'agente-marketing-slides@suntzu-475720.iam.gserviceaccount.com'

# 2. Reemplaza con el ID de la CARPETA DE DESTINO (donde quieres que se guarden los reportes).
# La ID es la parte final de la URL de la carpeta: https://drive.google.com/drive/folders/ESTA_ES_LA_ID
DESTINATION_FOLDER_ID = "1iK5K_j1nxOFo0zCrxfL-cHJeyZNlJqXj" 
# ---------------------

def check_drive_access():
    """Prueba la autenticación y los permisos de la cuenta de servicio."""
    print("--- 🔑 Probando Acceso de Service Account a Google Drive ---")
    
    if DESTINATION_FOLDER_ID == "ID_DE_LA_CARPETA_DE_DESTINO":
        print("❌ ERROR: Por favor, reemplaza 'ID_DE_LA_CARPETA_DE_DESTINO' con el ID real de tu carpeta en el script.")
        return
        
    try:
        # 1. Autenticación
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=creds)
        print(f"✅ Autenticación exitosa con: {SERVICE_ACCOUNT_EMAIL}")

        # 2. Prueba de Permisos (Listar archivos en la carpeta de destino)
        # Si la cuenta puede listar archivos, tiene permiso para crear/modificar en esa carpeta.
        
        # El q='...in parents' comprueba si la carpeta contiene archivos (y si la SA tiene acceso a la carpeta)
        results = service.files().list(
            q=f"'{DESTINATION_FOLDER_ID}' in parents and trashed = false",
            pageSize=5,
            fields="nextPageToken, files(id, name)"
        ).execute()
        
        items = results.get('files', [])

        print(f"\n--- Resultado de la Prueba en Carpeta ID: {DESTINATION_FOLDER_ID} ---")
        if items or results.get('nextPageToken') is not None or not results:
            print(f"🎉 ÉXITO: La Service Account tiene permisos de LECTURA/LISTADO sobre la carpeta.")
            print(f"   Esto confirma que tiene los permisos necesarios (Editor) para crear reportes.")
            if items:
                 print(f"   (Encontró {len(items)} archivos en la carpeta).")
        else:
            print("⚠️ ADVERTENCIA: La Service Account no pudo listar ningún archivo. Vuelve a verificar que el rol 'Editor' esté asignado al correo electrónico de la Service Account en la configuración de la carpeta.")

    except HttpError as error:
        # 403 Forbidden o 404 Not Found
        print(f"\n❌ ERROR DE DRIVE (CRÍTICO): {error}")
        if error.resp.status == 403:
            print("   -> 403 Forbidden: ¡Fallo de Permisos! Confirma que la carpeta o la plantilla estén compartidas con el Service Account como EDITOR.")
        elif error.resp.status == 404:
            print("   -> 404 Not Found: Confirma que el ID de la carpeta de destino es correcto.")
    except FileNotFoundError:
        print(f"\n❌ ERROR DE CONFIGURACIÓN: El archivo de credenciales '{SERVICE_ACCOUNT_FILE}' no se encontró.")
    except Exception as e:
        print(f"\n❌ ERROR DESCONOCIDO: {e}")

if __name__ == '__main__':
    check_drive_access()