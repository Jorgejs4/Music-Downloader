import os
import time
import re
from playwright.sync_api import sync_playwright

# ==============================
# 🔴 CONFIGURACIÓN
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(BASE_DIR, "spotify_session")

def run_exportify_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            slow_mo=500
        )
        
        page = browser.new_page()
        print("🌐 Entrando en Exportify...")
        page.goto("https://watsonbox.github.io/exportify/")
        
        # 0. Paso inicial: Pulsar el botón de comenzar si aparece
        try:
            # Buscamos el botón por ID exacto (#loginButton) o por el texto "Comenzar"
            start_button = page.locator("#loginButton")
            if start_button.count() == 0:
                start_button = page.get_by_role("button", name=re.compile(r"Comenzar|Get Started", re.IGNORECASE))
            
            if start_button.count() > 0:
                print("🚀 Pulsando botón de inicio (Comenzar)...")
                start_button.click()
        except Exception as e:
            print(f"ℹ No se encontró el botón de inicio o ya se saltó: {e}")

        # 1. Comprobar si hay que loguear
        if "Log In" in page.content():
            print("🔑 Por favor, inicia sesión en Spotify en la ventana que se ha abierto.")
            print("🕒 Tienes 2 minutos para loguearte...")
        
        # Esperamos a que la tabla aparezca (esto indica que ya estamos dentro)
        # Aumentamos el tiempo a 60 segundos para que cargue bien
        try:
            print("⏳ Esperando a que cargue tu lista de canciones...")
            page.wait_for_selector('table', timeout=60000)
            
            print("🔍 Buscando tus 'Liked Songs'...")
            # Buscamos la fila que dice 'Liked Songs' o 'Canciones que me gustan'
            # Usamos una expresión regular para que sea flexible con el idioma
            row = page.get_by_role("row").filter(has_text=re.compile(r"Liked Songs|Canciones que me gustan", re.IGNORECASE))
            
            # Si hay varias filas (raro), cogemos la primera
            export_button = row.locator('button:has-text("Export")').first
            
            print("📥 Iniciando descarga...")
            with page.expect_download() as download_info:
                export_button.click()
            
            download = download_info.value
            target_path = os.path.join(BASE_DIR, "playlist.csv")
            download.save_as(target_path)
            print(f"✅ ¡Éxito! Archivo guardado como: {target_path}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Asegúrate de haber iniciado sesión y de que aparezcan tus playlists.")
        
        browser.close()

if __name__ == "__main__":
    run_exportify_bot()
