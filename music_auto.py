import os
import json
import time
import shutil
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sys
import subprocess

# ==============================
# 🔴 CONFIGURACIÓN (ENV / EVITAR hardcodes)
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.join(BASE_DIR, "canciones_auto"))
DB_FILE = os.environ.get("DB_FILE", os.path.join(BASE_DIR, "downloaded.json"))
CSV_PATH = os.environ.get("CSV_PATH", os.path.join(BASE_DIR, "playlist.csv"))

SCOPE = "user-library-read"
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

OUTPUT_DIR = OUTPUT_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)

sp = None

# Cargar base de datos local
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        downloaded = set(json.load(f))
else:
    downloaded = set()

print("Obteniendo TODAS tus canciones con Me gusta...")

# Si no tienes credenciales, avisa y sale
if not (CLIENT_ID and CLIENT_SECRET):
    print("Configura SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET en variables de entorno.")
    sys.exit(1)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
))

current_liked = set()

results = sp.current_user_saved_tracks(limit=50)
tracks = results.get("items", [])

while results:
    for item in results["items"]:
        track = item["track"]
        name = track["name"]
        artist = track["artists"][0]["name"]
        identifier = f"{artist} - {name}"
        current_liked.add(identifier)
    if results.get("next"):
        results = sp.next(results)
    else:
        results = None

print(f"Total canciones en Spotify: {len(current_liked)}")

# ==============================
# 🎵 DESCARGAR NUEVAS
# ==============================
new_songs = current_liked - downloaded

print(f"Nuevas canciones detectadas: {len(new_songs)}")

for song in new_songs:
    print("Descargando:", song)
    artist, name = song.split(" - ", 1)
    # Llama al script principal para descargar una sola canción
    cmd = [sys.executable, os.path.join(BASE_DIR, "musicDownloader3.py"), "-a", artist, "-t", name, "--csv", CSV_PATH, "--output", OUTPUT_DIR]
    subprocess.run(cmd, check=False)
    time.sleep(1)

# ==============================
# 🗑️ ELIMINAR LAS QUE YA NO TIENEN LIKE
# ==============================
removed_songs = downloaded - current_liked

print(f"Canciones eliminadas de Spotify: {len(removed_songs)}")

for song in removed_songs:
    print("Eliminando:", song)
    artist, name = song.split(" - ", 1)
    artist_folder = os.path.join(OUTPUT_DIR, artist)
    if os.path.exists(artist_folder):
        for file in os.listdir(artist_folder):
            if name.lower() in file.lower():
                os.remove(os.path.join(artist_folder, file))
        if not os.listdir(artist_folder):
            shutil.rmtree(artist_folder)

# ==============================
# 💾 GUARDAR ESTADO ACTUAL
# ==============================
with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(list(current_liked), f, indent=2)

print("✔ Proceso completado correctamente.")
