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
        try:
            print("⏳ Esperando a que cargue tu lista de canciones...")
            page.wait_for_selector('table', timeout=60000)
            # Esperar un poco extra para que los datos se carguen en la tabla
            page.wait_for_timeout(2000)

            print("🔍 Buscando tus 'Liked Songs' / 'Canciones que me gustan'...")
            # Intentar encontrar la fila con varios nombres posibles
            patterns = [r"Liked Songs", r"Canciones que me gustan", r"Tus me gusta", r"Canciones que te gustan"]
            row = None
            for p in patterns:
                row_locator = page.get_by_role("row").filter(has_text=re.compile(p, re.IGNORECASE))
                if row_locator.count() > 0:
                    row = row_locator.first
                    print(f"✅ Encontrada fila con patrón: {p}")
                    break

            if not row:
                # Si no encuentra la fila específica, buscamos cualquier botón de exportar como último recurso
                print("⚠ No se encontró la fila específica, intentando buscar cualquier botón de exportar...")
                export_button = page.locator('button').filter(has_text=re.compile(r"Exportar|Export", re.IGNORECASE)).first
            else:
                # Buscamos el botón de Exportar/Export dentro de esa fila
                export_button = row.locator('button').filter(has_text=re.compile(r"Exportar|Export", re.IGNORECASE)).first

            if export_button.count() > 0:
                print("📥 Iniciando descarga...")
                with page.expect_download(timeout=60000) as download_info:
                    export_button.click()

                download = download_info.value
                target_path = os.path.join(BASE_DIR, "playlist.csv")
                download.save_as(target_path)
                print(f"✅ ¡Éxito! Archivo guardado como: {target_path}")
            else:
                print("❌ No se pudo encontrar el botón de Exportar.")

            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Asegúrate de haber iniciado sesión y de que aparezcan tus playlists.")
        
        browser.close()

if __name__ == "__main__":
    run_exportify_bot()
