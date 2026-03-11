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
# 🔴 CONFIGURACIÓN (v2.1 - Super Ninja Engine)
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
    print(f"🔍 Extrayendo canciones (Modo Invisible v2.1)...")
    
    try:
        playlist_id = url.split('/')[-1].split('?')[0]
        embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9'
        }
        
        response = requests.get(embed_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []

        # Intentar encontrar el JSON de metadatos (formato moderno)
        # Buscamos bloques que empiecen con {"tracks":
        matches = re.findall(r'({[^{]*?"tracks":.*?"items":.*?\]})', response.text)
        
        songs = []
        if matches:
            for m in matches:
                try:
                    data = json.loads(m)
                    items = data.get('tracks', {}).get('items', [])
                    for item in items:
                        track = item.get('track', item)
                        if track and 'name' in track:
                            songs.append({
                                "id": track.get('id') or track.get('uri'),
                                "title": track.get('name'),
                                "artist": track.get('artists')[0].get('name') if track.get('artists') else "Unknown Artist",
                                "album": track.get('album', {}).get('name', "Playlist")
                            })
                except: continue

        # Si el método A falla, intentamos el B (formato heredado)
        if not songs:
            match = re.search(r'<script id="resource" type="application/json">(.*?)</script>', response.text)
            if match:
                data = json.loads(match.group(1))
                items = data.get('tracks', {}).get('items', [])
                for item in items:
                    track = item.get('track', item)
                    songs.append({
                        "id": track.get('id'),
                        "title": track.get('name'),
                        "artist": track.get('artists')[0].get('name') if track.get('artists') else "Unknown Artist",
                        "album": track.get('album', {}).get('name', "Playlist")
                    })

        # Último recurso: escaneo manual de strings si todo lo demás falla
        if not songs:
            # Buscar patrones del tipo: "name":"NombreCancion","artists":[{"name":"Artista"}]
            found = re.findall(r'"name":"([^"]+?)","artists":\[{"name":"([^"]+?)"}\]', response.text)
            for title, artist in found:
                # Evitar duplicados y basura
                if title not in [s['title'] for s in songs]:
                    songs.append({
                        "id": f"{artist}-{title}",
                        "title": title,
                        "artist": artist,
                        "album": "Spotify Playlist"
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
            if song['id']:
                downloaded.add(song['id'])
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(downloaded), f, indent=4)
        except Exception as e:
            print(f"❌ Error descargando {song['title']}: {e}")

if __name__ == "__main__":
    sync()
