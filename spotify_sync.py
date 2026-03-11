import os
import json
import time
import sys
import subprocess
import re
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==============================
# 🔴 CONFIGURACIÓN (v3.0 - Direct Sync No-API)
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "downloaded.json")
MAIN_SCRIPT = os.path.join(BASE_DIR, "musicDownloader3.py")
PLAYLIST_URL = os.environ.get("SPOTIFY_PLAYLIST_URL")

# Cargar base de datos local
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            downloaded = set(json.load(f))
    except:
        downloaded = set()
else:
    downloaded = set()

def get_songs_via_spotdl_direct(url):
    """Extrae la lista de canciones usando spotdl directamente (sin bloqueos de API)"""
    print(f"🔍 Escaneando Playlist (1000+ canciones)...")
    
    # Limpiamos el enlace
    clean_url = url.split('?')[0]
    
    # Usamos spotdl para obtener los metadatos de TODA la lista en un archivo temporal
    temp_json = os.path.join(BASE_DIR, "playlist_data.spotdl")
    
    # Este comando es la clave: extrae metadatos sin descargar
    cmd = ["spotdl", "save", clean_url, "--save-file", temp_json]
    
    try:
        # Ejecutamos spotdl. Si falla por rate limit, lo reintentamos con un delay
        print("⏳ Conectando con los servidores de metadatos...")
        subprocess.run(cmd, check=True)
        
        if not os.path.exists(temp_json):
            return []
            
        with open(temp_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        songs = []
        for track in data:
            songs.append({
                "id": track.get("url"), # URL de spotify como ID único
                "title": track.get("name"),
                "artist": track.get("artists")[0] if track.get("artists") else "Unknown",
                "album": track.get("album_name", "Spotify Playlist")
            })
            
        os.remove(temp_json)
        return songs
    except Exception as e:
        print(f"❌ Error al escanear: {e}")
        return []

def sync():
    if not PLAYLIST_URL:
        print("❌ ERROR: Configura SPOTIFY_PLAYLIST_URL en tu .env")
        return

    all_songs = get_songs_via_spotdl_direct(PLAYLIST_URL)
    
    if not all_songs:
        print("ℹ No se pudieron obtener canciones. Asegúrate de que la playlist sea PÚBLICA.")
        return

    new_songs = [s for s in all_songs if s['id'] not in downloaded]

    print(f"✅ Total en Spotify: {len(all_songs)}")
    print(f"🚀 Canciones nuevas para descargar: {len(new_songs)}")

    # Para evitar bloqueos, descargamos de una en una con un pequeño respiro
    for i, song in enumerate(new_songs):
        print(f"\n[ {i+1} / {len(new_songs)} ] Procesando: {song['artist']} - {song['title']}")
        
        cmd = [
            sys.executable, MAIN_SCRIPT,
            "-a", song['artist'],
            "-t", song['title'],
            "--album", song['album'],
            "--send"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            downloaded.add(song['id'])
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(list(downloaded), f, indent=4)
            # Pequeña pausa para no saturar YouTube
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error en {song['title']}: {e}")

if __name__ == "__main__":
    sync()
