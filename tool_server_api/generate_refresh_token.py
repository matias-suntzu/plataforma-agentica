import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Ruta a tu archivo credentials.json (descargado desde Google Cloud Console)
CLIENT_SECRETS_FILE = "client_secret.json"

# Scopes necesarios para Google Ads API
SCOPES = ["https://www.googleapis.com/auth/adwords"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=8080, prompt="consent", authorization_prompt_message="")

    print("\n✅ Access Token:", credentials.token)
    print("\n🔁 Refresh Token:", credentials.refresh_token)
    print("\n🧩 Client ID:", credentials.client_id)
    print("\n🔐 Client Secret:", credentials.client_secret)

if __name__ == "__main__":
    main()
