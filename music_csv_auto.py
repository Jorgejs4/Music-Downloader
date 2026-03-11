import os
import json
import time
import csv
import sys
import subprocess
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==============================
# 🔴 CONFIGURACIÓN
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.join(BASE_DIR, "canciones_auto"))
DB_FILE = os.environ.get("DB_FILE", os.path.join(BASE_DIR, "downloaded.json"))
CSV_FILE = os.path.join(BASE_DIR, "playlist.csv") # El archivo que descargues de Exportify

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cargar base de datos local
if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            downloaded = set(json.load(f))
    except (json.JSONDecodeError, ValueError):
        print("⚠ Base de datos dañada, se reseteará.")
        downloaded = set()
else:
    downloaded = set()

if not os.path.exists(CSV_FILE):
    print(f"❌ ERROR: No encuentro el archivo '{CSV_FILE}'")
    print("Por favor, descarga tus 'Liked Songs' desde Exportify, pon el archivo aquí y llámalo 'playlist.csv'")
    sys.exit(1)

print(f"📖 Leyendo canciones desde {CSV_FILE}...")

current_songs = []

with open(CSV_FILE, mode='r', encoding='utf-8') as f:
    # Exportify suele usar estos nombres de columna
    reader = csv.DictReader(f)
    for row in reader:
        # Intentamos detectar los nombres de las columnas (pueden variar según la herramienta)
        title = row.get("Nombre de la canción") or row.get("Track Name") or row.get("Name") or row.get("track_name")
        artist = row.get("Nombre(s) del artista") or row.get("Artist Name(s)") or row.get("Artist") or row.get("artist_name")
        album = row.get("Nombre del álbum") or row.get("Album Name") or row.get("Album") or row.get("album_name") or "Unknown Album"

        
        if title and artist:
            identifier = f"{artist.strip()} - {title.strip()}"
            current_songs.append({
                "id": identifier,
                "artist": artist.strip(),
                "title": title.strip(),
                "album": album.strip()
            })

print(f"✅ Total canciones encontradas en el CSV: {len(current_songs)}")

# ==============================
# 🎵 PROCESAR CANCIONES
# ==============================
new_count = 0
for song in current_songs:
    if song["id"] in downloaded:
        continue
    
    new_count += 1
    print(f"⬇️ [{new_count}] Descargando y enviando: {song['id']}")
    
    cmd = [
        sys.executable, 
        os.path.join(BASE_DIR, "musicDownloader3.py"), 
        "-a", song["artist"], 
        "-t", song["title"], 
        "--album", song["album"],
        "--send"
    ]
    
    # Ejecutar la descarga
    result = subprocess.run(cmd, check=False)
    
    # Marcar como descargada y guardar progreso
    downloaded.add(song["id"])
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(list(downloaded), f, indent=2)
    
    time.sleep(1)

if new_count == 0:
    print("✨ Todas las canciones ya estaban descargadas.")
else:
    print(f"✔ ¡Proceso completado! Se han procesado {new_count} canciones nuevas.")
