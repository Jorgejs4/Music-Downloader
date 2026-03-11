import os
import json
import time
import sys
import subprocess
import requests
import re
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==============================
# 🔴 CONFIGURACIÓN (v2.0 - Ninja Embed Engine)
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

def get_songs_via_embed(url):
    """Extrae canciones directamente del Embed de Spotify (sin API, sin Premium)"""
    print(f"🔍 Extrayendo canciones (Modo Invisible)...")
    
    try:
        # Extraer ID de la playlist
        playlist_id = url.split('/')[-1].split('?')[0]
        embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        
        response = requests.get(embed_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ Error al acceder a Spotify (Status {response.status_code})")
            return []

        # Buscar el JSON de la playlist en el código HTML
        # Spotify guarda los datos en un script de tipo application/json
        match = re.search(r'<script id="resource" type="application/json">(.*?)</script>', response.text)
        
        if not match:
            # Intento secundario: buscar cualquier bloque de JSON que contenga tracks
            match = re.search(r'{"track":.*?"uri":".*?"}', response.text)
            if not match:
                print("❌ No se pudo encontrar la lista de canciones en la página.")
                return []
            
        data = json.loads(match.group(1))
        
        # Estructura del Embed de Spotify
        tracks_data = data.get('tracks', {}).get('items', [])
        if not tracks_data and 'track' in data: # Caso de un solo track o estructura distinta
            tracks_data = [data]

        songs = []
        for item in tracks_data:
            track = item.get('track', item)
            if not track: continue
            
            songs.append({
                "id": track.get('id') or track.get('uri'),
                "title": track.get('name'),
                "artist": track.get('artists')[0].get('name') if track.get('artists') else "Unknown Artist",
                "album": track.get('album', {}).get('name', "Spotify Playlist")
            })
            
        return songs
    except Exception as e:
        print(f"❌ Error de extracción: {e}")
        return []

def sync():
    if not PLAYLIST_URL:
        print("❌ ERROR: Configura SPOTIFY_PLAYLIST_URL en tu .env")
        return

    all_songs = get_songs_via_embed(PLAYLIST_URL)
    
    if not all_songs:
        print("ℹ No se pudieron obtener canciones. Comprueba que la playlist sea PÚBLICA.")
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
            # Registrar como descargada
            if song['id']:
                downloaded.add(song['id'])
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(downloaded), f, indent=4)
        except Exception as e:
            print(f"❌ Error descargando {song['title']}: {e}")

if __name__ == "__main__":
    sync()
