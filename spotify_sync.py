import os
import json
import time
import builtins
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sys
import subprocess
from dotenv import load_dotenv

# Monkeypatch para corregir bug de spotipy en Python 3.13+
if not hasattr(builtins, 'raw_input'):
    builtins.raw_input = builtins.input

# Cargar variables de entorno
load_dotenv()

# ==============================
# 🔴 CONFIGURACIÓN
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "downloaded.json")
MAIN_SCRIPT = os.path.join(BASE_DIR, "musicDownloader3.py")

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
PLAYLIST_ID = os.environ.get("SPOTIFY_PLAYLIST_ID")
SCOPE = "user-library-read playlist-read-private"

# Cargar base de datos local de canciones ya descargadas
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            downloaded = set(json.load(f))
    except:
        downloaded = set()
else:
    downloaded = set()

def get_songs(sp):
    """Obtiene canciones de 'Liked Songs' o de una Playlist específica"""
    results = []
    offset = 0
    
    if PLAYLIST_ID:
        print(f"🔍 Obteniendo canciones de la Playlist: {PLAYLIST_ID}...")
        while True:
            response = sp.playlist_items(PLAYLIST_ID, limit=50, offset=offset)
            if not response['items']: break
            for item in response['items']:
                track = item['track']
                if not track: continue # Evitar errores con tracks borrados
                results.append({
                    "id": track['id'],
                    "title": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name']
                })
            offset += len(response['items'])
            print(f"📦 Cargadas {offset} canciones...")
    else:
        print("🔍 Obteniendo tus 'Canciones que me gustan'...")
        while True:
            response = sp.current_user_saved_tracks(limit=50, offset=offset)
            if not response['items']: break
            for item in response['items']:
                track = item['track']
                results.append({
                    "id": track['id'],
                    "title": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name']
                })
            offset += len(response['items'])
            print(f"📦 Cargadas {offset} canciones...")
            
    return results

def sync():
    if not (CLIENT_ID and CLIENT_SECRET):
        print("❌ ERROR: Configura SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET en tu .env")
        return

    # Autenticación
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        open_browser=False
    ))

    try:
        all_songs = get_songs(sp)
    except Exception as e:
        print(f"❌ Error al obtener canciones de Spotify: {e}")
        if "403" in str(e):
            print("\n💡 TIP: Spotify está bloqueando el acceso a 'Liked Songs'.")
            print("Crea una Playlist, pon tus canciones ahí y añade SPOTIFY_PLAYLIST_ID a tu .env")
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
            "--send" # En Termux esto disparará el guardado local y escaneo de medios
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
