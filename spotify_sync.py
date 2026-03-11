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
# 🔴 CONFIGURACIÓN (v2.2 - Deep Scanner Engine)
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
    print(f"🔍 Extrayendo canciones (Modo Invisible v2.2)...")
    
    try:
        playlist_id = url.split('/')[-1].split('?')[0]
        embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Referer': 'https://open.spotify.com/'
        }
        
        response = requests.get(embed_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}")
            return []

        songs = []
        
        # Método 1: Búsqueda de bloques JSON estructurados (Resource)
        json_matches = re.findall(r'<script id="resource" type="application/json">(.*?)</script>', response.text)
        if not json_matches:
            # Método 1.1: Búsqueda de bloques JSON en cualquier script
            json_matches = re.findall(r'({[^{]*?"tracks":.*?"items":.*?\]})', response.text)

        for m in json_matches:
            try:
                data = json.loads(m)
                # Navegar por la estructura del JSON buscando tracks
                # Soporta múltiples variantes de la estructura de Spotify
                items = []
                if 'tracks' in data and 'items' in data['tracks']:
                    items = data['tracks']['items']
                elif 'items' in data:
                    items = data['items']
                
                for item in items:
                    track = item.get('track', item)
                    if track and 'name' in track:
                        songs.append({
                            "id": track.get('id') or track.get('uri') or track.get('name'),
                            "title": track.get('name'),
                            "artist": track.get('artists', [{}])[0].get('name') or "Unknown Artist",
                            "album": track.get('album', {}).get('name', "Playlist")
                        })
            except: continue

        # Método 2: Escaneo de patrones de texto (Failsafe)
        # Busca patrones como "name":"Song Name","artists":[{"name":"Artist Name"}]
        if not songs:
            # Esta regex es muy potente para capturar pares título-artista en el JS ofuscado
            pattern = r'"name":"([^"]+?)","artists":\[{"name":"([^"]+?)"}\]'
            found = re.findall(pattern, response.text)
            for title, artist in found:
                if title not in [s['title'] for s in songs] and title != "Spotify":
                    songs.append({
                        "id": f"{artist}-{title}".replace(" ", "_"),
                        "title": title,
                        "artist": artist,
                        "album": "Spotify Playlist"
                    })

        # Método 3: Escaneo de títulos y artistas en el HTML renderizado (Failsafe final)
        if not songs:
            # Buscar patrones de texto plano que Spotify a veces deja en el HTML
            # ej: <span>Song Title</span><span>Artist Name</span>
            pattern_html = r'<span[^>]*>([^<]+)</span>.*?<span[^>]*>([^<]+)</span>'
            found_html = re.findall(pattern_html, response.text)
            for title, artist in found_html:
                if len(title) > 1 and len(artist) > 1:
                    songs.append({
                        "id": f"{artist}-{title}".replace(" ", "_"),
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
