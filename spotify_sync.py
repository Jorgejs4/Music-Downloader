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
# 🔴 CONFIGURACIÓN
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "downloaded.json")
MAIN_SCRIPT = os.path.join(BASE_DIR, "musicDownloader3.py")

# El usuario puede poner el ID o la URL completa
PLAYLIST_INPUT = os.environ.get("SPOTIFY_PLAYLIST_URL") or os.environ.get("SPOTIFY_PLAYLIST_ID")

# Cargar base de datos local
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            downloaded = set(json.load(f))
    except:
        downloaded = set()
else:
    downloaded = set()

def get_songs_via_ytdlp(playlist_url):
    """Usa yt-dlp para obtener los nombres de las canciones sin usar la API de Spotify"""
    print(f"🔍 Extrayendo canciones de la Playlist: {playlist_url}...")
    print("⏳ Esto puede tardar unos segundos según el tamaño de la lista...")
    
    # Limpiar el enlace si tiene ?si=...
    clean_url = playlist_url.split('?')[0]
    if not clean_url.startswith('http'):
        clean_url = f"https://open.spotify.com/playlist/{clean_url}"

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--quiet",
        clean_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        songs = []
        for entry in data.get('entries', []):
            # yt-dlp suele devolver el título como "Artista - Canción" en Spotify
            title_full = entry.get('title', 'Unknown')
            # Intentar separar artista y título si es posible
            if " - " in title_full:
                artist, title = title_full.split(" - ", 1)
            else:
                artist, title = "Unknown Artist", title_full
            
            songs.append({
                "id": entry.get('id') or entry.get('url'), # Usamos el ID de spotify que nos da yt-dlp
                "title": title.strip(),
                "artist": artist.strip(),
                "album": "Spotify Playlist"
            })
        return songs
    except Exception as e:
        print(f"❌ Error al usar yt-dlp: {e}")
        return []

def sync():
    if not PLAYLIST_INPUT:
        print("❌ ERROR: Configura SPOTIFY_PLAYLIST_URL en tu .env")
        print("Ejemplo: SPOTIFY_PLAYLIST_URL=https://open.spotify.com/playlist/tu_id")
        return

    all_songs = get_songs_via_ytdlp(PLAYLIST_INPUT)
    
    if not all_songs:
        print("ℹ No se encontraron canciones. Asegúrate de que la playlist sea PÚBLICA.")
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
            if song['id']:
                downloaded.add(song['id'])
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(downloaded), f, indent=4)
        except Exception as e:
            print(f"❌ Error descargando {song['title']}: {e}")

if __name__ == "__main__":
    sync()
