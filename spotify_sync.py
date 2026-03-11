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
# 🔴 CONFIGURACIÓN (v2.3 - Unlimited Sync)
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "downloaded.json")
MAIN_SCRIPT = os.path.join(BASE_DIR, "musicDownloader3.py")

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
PLAYLIST_ID = os.environ.get("SPOTIFY_PLAYLIST_ID")
# Scopes necesarios para leer listas privadas/públicas
SCOPE = "user-library-read playlist-read-private playlist-read-collaborative"

# Cargar base de datos local
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            downloaded = set(json.load(f))
    except:
        downloaded = set()
else:
    downloaded = set()

def get_all_songs(sp):
    """Obtiene TODAS las canciones de una Playlist o Liked Songs usando paginación"""
    results = []
    offset = 0
    limit = 50
    
    if PLAYLIST_ID:
        print(f"🔍 Extrayendo canciones de la Playlist: {PLAYLIST_ID}...")
        while True:
            response = sp.playlist_items(PLAYLIST_ID, limit=limit, offset=offset)
            if not response['items']: break
            for item in response['items']:
                track = item.get('track')
                if not track: continue
                results.append({
                    "id": track['id'],
                    "title": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name']
                })
            offset += len(response['items'])
            print(f"📦 Cargadas {offset} canciones...")
    else:
        print("🔍 Extrayendo tus 'Canciones que me gustan'...")
        while True:
            response = sp.current_user_saved_tracks(limit=limit, offset=offset)
            if not response['items']: break
            for item in response['items']:
                track = item.get('track')
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

    # Autenticación (Modo caché para evitar login repetido)
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        open_browser=False,
        cache_path=os.path.join(BASE_DIR, ".cache-spotify")
    )
    
    sp = spotipy.Spotify(auth_manager=auth_manager)

    try:
        all_songs = get_all_songs(sp)
    except Exception as e:
        print(f"❌ Error de Spotify: {e}")
        if "403" in str(e):
            print("\n💡 TIP: Para evitar el error 403 (Premium Required):")
            print("1. Crea una Playlist normal en Spotify.")
            print("2. Mete tus canciones allí.")
            print("3. Pon el ID de esa playlist en tu .env (SPOTIFY_PLAYLIST_ID)")
        return

    new_songs = [s for s in all_songs if s['id'] not in downloaded]

    print(f"✅ Total en Spotify: {len(all_songs)}")
    print(f"🚀 Canciones nuevas para descargar: {len(new_songs)}")

    for i, song in enumerate(new_songs):
        print(f"\n[ {i+1} / {len(new_songs)} ] Descargando: {song['artist']} - {song['title']}")
        
        cmd = [
            sys.executable, MAIN_SCRIPT,
            "-a", song['artist'],
            "-t", song['title'],
            "--album", song['album'],
            "--send"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            if song['id']:
                downloaded.add(song['id'])
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(downloaded), f, indent=4)
        except Exception as e:
            print(f"❌ Error en descarga: {e}")

if __name__ == "__main__":
    sync()
