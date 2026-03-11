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

def run_sync():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 Lanzando robot de Exportify...")
    try:
        # Llamar al bot de Exportify
        # Importamos aquí para evitar errores si no se ha instalado playwright
        from exportify_bot import run_exportify_bot
        run_exportify_bot()
    except Exception as e:
        print(f"⚠ El robot de Exportify ha fallado o requiere intervención: {e}")

    if os.path.exists(PROJECT_CSV):
        # Ejecutar el script de descarga
        print("🚀 Iniciando descarga y envío al móvil...")
        subprocess.run([sys.executable, MAIN_SCRIPT], check=True)
    else:
        print("ℹ No se encontró 'playlist.csv' tras la descarga del robot.")

if __name__ == "__main__":
    # Si se ejecuta directamente, hace una pasada
    run_sync()
