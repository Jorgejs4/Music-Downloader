import os
import shutil
import time
import subprocess
import sys
from datetime import datetime

# ==============================
# 🔴 CONFIGURACIÓN
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(os.environ['USERPROFILE'], 'Downloads')
PROJECT_CSV = os.path.join(BASE_DIR, 'playlist.csv')
MAIN_SCRIPT = os.path.join(BASE_DIR, 'music_csv_auto.py')

def find_latest_exportify_csv():
    """Busca el archivo CSV más reciente de Spotify en Descargas"""
    files = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith('.csv') and ('liked_songs' in f.lower() or 'playlist' in f.lower() or 'spotify' in f.lower())]
    if not files:
        return None
    
    # Ordenar por fecha de creación para coger el último
    files_with_path = [os.path.join(DOWNLOADS_DIR, f) for f in files]
    latest_file = max(files_with_path, key=os.path.getctime)
    return latest_file

def send_csv_to_phone():
    """Envía el archivo playlist.csv al móvil vía ADB"""
    if not os.path.exists(PROJECT_CSV):
        return
    
    print("📲 Enviando playlist.csv al móvil vía ADB...")
    try:
        # Verificar si hay dispositivos
        res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "device" not in res.stdout.splitlines()[1] if len(res.stdout.splitlines()) > 1 else "":
            print("⚠ No hay móvil detectado por ADB. Saltando envío de CSV.")
            return

        # Enviar el archivo a la carpeta de descargas de Android
        dest = "/sdcard/Download/playlist.csv"
        subprocess.run(["adb", "push", PROJECT_CSV, dest], check=True)
        print(f"✅ CSV enviado correctamente a: {dest}")

        # --- AUTO-ARRANQUE EN MÓVIL ---
        print("🚀 Lanzando descarga en el móvil automáticamente...")
        # 1. Abrir Termux
        subprocess.run(["adb", "shell", "am", "start", "-n", "com.termux/.TermuxActivity"], check=True)
        time.sleep(2) # Esperar a que abra
        # 2. Escribir el comando y pulsar Enter (simulado)
        # Usamos %s para representar espacios en algunos comandos adb o escapamos espacios
        cmd_mvl = "cd Music-Downloader && python music_csv_auto.py"
        # Escapamos los espacios para el comando 'input text'
        cmd_escaped = cmd_mvl.replace(" ", "\\ ")
        subprocess.run(["adb", "shell", "input", "text", cmd_escaped], check=True)
        subprocess.run(["adb", "shell", "input", "keyevent", "66"], check=True) # 66 es ENTER
        print("✅ ¡Móvil activado y descargando!")

    except Exception as e:
        print(f"❌ Error al interactuar con el móvil por ADB: {e}")

def run_sync():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 Lanzando robot de Exportify...")
    try:
        # Llamar al bot de Exportify
        from exportify_bot import run_exportify_bot
        run_exportify_bot()
    except Exception as e:
        print(f"⚠ El robot de Exportify ha fallado o requiere intervención: {e}")

    if os.path.exists(PROJECT_CSV):
        # Nuevo paso: Enviar al móvil
        send_csv_to_phone()
        
        # Ejecutar el script de descarga en el PC (opcional si ya lo vas a hacer en el móvil)
        print("🚀 Iniciando descarga en el PC...")
        subprocess.run([sys.executable, MAIN_SCRIPT], check=True)
    else:
        print("ℹ No se encontró 'playlist.csv' tras la descarga del robot.")

if __name__ == "__main__":
    # Si se ejecuta directamente, hace una pasada
    run_sync()
