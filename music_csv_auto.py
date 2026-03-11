import os
import json
import time
import csv
import sys
import subprocess
import shutil
import re
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==============================
# 🔴 CONFIGURACIÓN (v6.0 - Auto-CSV Mobile)
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Detectar si estamos en Android para buscar en la carpeta de descargas del sistema
IS_ANDROID = os.path.exists("/sdcard")
DOWNLOADS_DIR = "/sdcard/Download" if IS_ANDROID else os.path.join(os.path.expanduser("~"), "Downloads")
PROJECT_CSV = os.path.join(BASE_DIR, "playlist.csv")
DB_FILE = os.path.join(BASE_DIR, "downloaded.json")
MAIN_SCRIPT = os.path.join(BASE_DIR, "musicDownloader3.py")

def find_and_move_csv():
    """Busca un archivo CSV de Spotify en la carpeta de descargas del móvil, priorizando números altos (1), (2)..."""
    if not IS_ANDROID: return False
    
    print(f"🔍 Buscando nuevos archivos CSV en {DOWNLOADS_DIR}...")
    # Filtro básico de archivos CSV que parecen ser de Spotify
    pattern_files = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith('.csv') and ('spotify' in f.lower() or 'playlist' in f.lower() or 'liked' in f.lower())]
    
    if not pattern_files:
        return False
    
    # Lógica para detectar el número entre paréntesis
    def extract_number(filename):
        match = re.search(r'\((\d+)\)', filename)
        return int(match.group(1)) if match else 0

    # Ordenar primero por el número en el nombre (descendente) y luego por fecha de creación
    pattern_files.sort(key=lambda x: (extract_number(x), os.path.getctime(os.path.join(DOWNLOADS_DIR, x))), reverse=True)
    
    latest_file = os.path.join(DOWNLOADS_DIR, pattern_files[0])
    print(f"📦 Encontrado archivo más reciente (Prioridad: número alto): {os.path.basename(latest_file)}")
    
    try:
        shutil.move(latest_file, PROJECT_CSV)
        print(f"✅ Movido y renombrado a: {PROJECT_CSV}")
        return True
    except Exception as e:
        print(f"❌ Error al mover el archivo: {e}")
        return False

def process_csv():
    if not os.path.exists(PROJECT_CSV):
        if not find_and_move_csv():
            print("❌ ERROR: No se encuentra 'playlist.csv' ni archivos nuevos en Descargas.")
            print("💡 TIP: Entra en Exportify desde tu Chrome, descarga el CSV y vuelve aquí.")
            return

    # Cargar base de datos local
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                downloaded = set(json.load(f))
        except:
            downloaded = set()
    else:
        downloaded = set()

    print(f"📖 Leyendo canciones desde {PROJECT_CSV}...")
    
    songs = []
    with open(PROJECT_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("Nombre de la canción") or row.get("Track Name") or row.get("Name")
            artist = row.get("Nombre(s) del artista") or row.get("Artist Name(s)") or row.get("Artist")
            album = row.get("Nombre del álbum") or row.get("Album Name") or "Unknown Album"
            track_id = row.get("URL de la canción") or f"{artist}-{title}"
            
            if title and artist:
                songs.append({"id": track_id, "title": title, "artist": artist, "album": album})

    new_songs = [s for s in songs if s['id'] not in downloaded]
    print(f"✅ Total: {len(songs)} | 🚀 Nuevas: {len(new_songs)}")

    for i, song in enumerate(new_songs):
        print(f"\n[ {i+1} / {len(new_songs)} ] Descargando: {song['artist']} - {song['title']}")
        cmd = [sys.executable, MAIN_SCRIPT, "-a", song['artist'], "-t", song['title'], "--album", song['album'], "--send"]
        
        try:
            subprocess.run(cmd, check=True)
            downloaded.add(song['id'])
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(list(downloaded), f, indent=4)
        except:
            print(f"❌ Error en {song['title']}")

if __name__ == "__main__":
    process_csv()
