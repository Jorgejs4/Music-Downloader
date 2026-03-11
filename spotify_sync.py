import os
import json
import time
import sys
import subprocess
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==============================
# 🔴 CONFIGURACIÓN
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "downloaded.json")
MAIN_SCRIPT = os.path.join(BASE_DIR, "musicDownloader3.py")

# El usuario pone el enlace de la playlist en el .env
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

def get_songs_via_spotdl(url):
    """Usa spotdl para obtener los metadatos de la playlist en JSON"""
    print(f"🔍 Extrayendo canciones de la Playlist con spotdl...")
    temp_json = os.path.join(BASE_DIR, "temp_playlist.spotdl")
    
    # Comando para guardar los metadatos en un archivo JSON sin descargar nada
    cmd = ["spotdl", "save", url, "--save-file", temp_json]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if not os.path.exists(temp_json):
            return []
            
        with open(temp_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        songs = []
        for track in data:
            songs.append({
                "id": track.get("url") or track.get("name"),
                "title": track.get("name"),
                "artist": track.get("artists")[0] if track.get("artists") else "Unknown Artist",
                "album": track.get("album_name", "Unknown Album")
            })
            
        # Limpiar temporal
        os.remove(temp_json)
        return songs
    except Exception as e:
        print(f"❌ Error al usar spotdl: {e}")
        if "not found" in str(e).lower():
            print("💡 TIP: Ejecuta 'pip install spotdl' en Termux primero.")
        return []

def sync():
    if not PLAYLIST_URL:
        print("❌ ERROR: Configura SPOTIFY_PLAYLIST_URL en tu .env")
        return

    all_songs = get_songs_via_spotdl(PLAYLIST_URL)
    
    if not all_songs:
        print("ℹ No se pudieron obtener canciones. Comprueba el enlace y tu conexión.")
        return

    new_songs = [s for s in all_songs if s['id'] not in downloaded]

    print(f"✅ Total en Spotify: {len(all_songs)}")
    print(f"🚀 Canciones nuevas para descargar: {len(new_songs)}")

    for i, song in enumerate(new_songs):
        print(f"\n[ {i+1} / {len(new_songs)} ] Descargando: {song['artist']} - {song['title']}")
        
        # Llamar al descargador principal
        cmd = [
            sys.executable, MAIN_SCRIPT,
            "-a", song['artist'],
            "-t", song['title'],
            "--album", song['album'],
            "--send"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            # Registrar como descargada
            downloaded.add(song['id'])
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(list(downloaded), f, indent=4)
        except Exception as e:
            print(f"❌ Error descargando {song['title']}: {e}")

if __name__ == "__main__":
    sync()
