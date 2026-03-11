#!/usr/bin/env python3
"""
Music Downloader 4.0 - Profesional (Versión con ADB)
==================================
- Descarga MP3 desde YouTube con portada
- Guarda portada embebida + .jpg
- Letra normal embebida (Genius)
- Letra sincronizada .lrc (lrclib o generada)
- Carpeta: Artista Principal / Álbum
- Descarga en paralelo 4 canciones
- Compatible Android / Retro Music
- ENVÍO AUTOMÁTICO A MÓVIL VÍA ADB
"""

import os, re, csv, time, logging, subprocess, shutil
import requests, lyricsgenius
from mutagen.id3 import ID3, TIT2, TPE1, TALB, USLT, APIC
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Cargar configuración desde .env
load_dotenv()

# ─── DETECCIÓN DE ENTORNO ──────────────────────────────────
IS_ANDROID = os.path.exists("/sdcard") and shutil.which("termux-setup-storage") is not None

# ─── CONFIG ────────────────────────────────────────────────
GENIUS_TOKEN = os.environ.get("GENIUS_TOKEN")
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CSV_PATH     = os.environ.get("CSV_PATH", os.path.join(BASE_DIR, "playlist.csv"))
# En Android, preferimos una carpeta de sistema
if IS_ANDROID:
    OUTPUT_DIR = os.path.join("/sdcard", "Music", "music downloader")
else:
    OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.join(BASE_DIR, "canciones_auto"))

PHONE_DEST   = "/sdcard/Music/music downloader/"
SKIP_EXISTING = True
MAX_THREADS   = 4

# ─── LOGGING ───────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─── UTILITIES ────────────────────────────────────────────
def sanitize(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def first_artist(artist_field: str) -> str:
    separators = [",", ";", "&", " feat.", " ft.", " x ", " X "]
    artist = artist_field
    for sep in separators:
        if sep in artist:
            artist = artist.split(sep)[0]
    return artist.strip()

def clean_title(title: str) -> str:
    patterns = [r"\(.*?remaster.*?\)", r"\(.*?live.*?\)", r"\(.*?version.*?\)",
                r"\(.*?\)", r"\[.*?\]", r"- live.*", r"- remaster.*"]
    clean = title
    for p in patterns:
        clean = re.sub(p, "", clean, flags=re.IGNORECASE)
    return clean.strip()

def get_song_dir(base, artist, album):
    folder = os.path.join(base, sanitize(artist), sanitize(album))
    os.makedirs(folder, exist_ok=True)
    return folder

# ─── MEDIA SCAN ────────────────────────────────────────────
def scan_media(path):
    """Notifica al sistema Android que hay un nuevo archivo de medios"""
    if IS_ANDROID and shutil.which("termux-media-scan"):
        subprocess.run(["termux-media-scan", path], capture_output=True)
    elif not IS_ANDROID:
        # Si no es Android, no hacemos nada (es local en PC)
        pass

# ─── ADB SEND / LOCAL MOVE ─────────────────────────────────
def send_to_mobile(local_path, artist, album):
    if IS_ANDROID:
        # Si ya estamos en Android, el archivo ya está en su sitio (OUTPUT_DIR es /sdcard/...)
        log.info(f"✓ Archivo guardado localmente en Android: {os.path.basename(local_path)}")
        scan_media(local_path)
        return True

    try:
        # Lógica original de ADB para PC
        res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = res.stdout.splitlines()[1:]
        
        device_serial = None
        for line in lines:
            if "\tdevice" in line:
                device_serial = line.split("\t")[0].strip()
                break
        
        if not device_serial:
            log.warning("⚠ No hay móvil detectado por ADB. Saltando envío.")
            return False
        
        dest_folder = f"{PHONE_DEST}{sanitize(artist)}/{sanitize(album)}/"
        subprocess.run(["adb", "-s", device_serial, "shell", f"mkdir -p '{dest_folder}'"], check=False)
        
        filename = os.path.basename(local_path)
        dest = dest_folder + filename
        log.info(f"Enviando a móvil ({device_serial}): {filename} -> {dest_folder} ...")
        subprocess.run(["adb", "-s", device_serial, "push", local_path, dest], check=True)
        
        lrc_local = os.path.splitext(local_path)[0] + ".lrc"
        if os.path.exists(lrc_local):
            lrc_filename = os.path.basename(lrc_local)
            lrc_dest = dest_folder + lrc_filename
            log.info(f"Enviando letra sincronizada: {lrc_filename} ...")
            subprocess.run(["adb", "-s", device_serial, "push", lrc_local, lrc_dest], check=True)

        subprocess.run(["adb", "-s", device_serial, "shell", f"am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d 'file://{dest}'"], capture_output=True)
        
        return True
    except Exception as e:
        log.error(f"Error ADB: {e}")
        return False

# ─── DESCARGA Y PORTADA ────────────────────────────────────
def download_mp3(track):
    title, artist, album = track["title"], track["artist"], track["album"]
    safe_name = sanitize(f"{artist} - {title}")
    song_dir = get_song_dir(OUTPUT_DIR, artist, album)
    mp3_path = os.path.join(song_dir, f"{safe_name}.mp3")
    
    if SKIP_EXISTING and os.path.exists(mp3_path):
        log.info(f"{artist} - {title} ✓ Ya existe localmente")
        # Asegurarnos de que track tenga la info correcta
        return mp3_path, track

    query = f"{artist} - {title} official audio"
    output_tpl = os.path.join(song_dir, f"{safe_name}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_tpl,
        "noplaylist": True,
        "quiet": True,
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"},
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"},
        ],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])
        if os.path.exists(mp3_path):
            return mp3_path, track
        else:
            return None, track
    except Exception as e:
        log.error(f"{artist} - {title} ERROR: {e}")
        return None, track

# ─── METADATOS ─────────────────────────────────────────────
def embed_tags(mp3_path, track, lyrics=None, synced=None):
    try:
        audio = ID3(mp3_path)
    except:
        audio = ID3()
    audio.delall("TIT2"); audio.delall("TPE1"); audio.delall("TALB"); audio.delall("USLT")
    audio.add(TIT2(encoding=3, text=track["title"]))
    audio.add(TPE1(encoding=3, text=track["artist"]))
    audio.add(TALB(encoding=3, text=track["album"]))
    if lyrics: audio.add(USLT(encoding=3, lang="spa", text=lyrics))
    audio.save(mp3_path, v2_version=3)
    
    if synced:
        lrc_path = os.path.splitext(mp3_path)[0] + ".lrc"
        with open(lrc_path, "w", encoding="utf-8") as f: f.write(synced)

# ─── LETRAS ───────────────────────────────────────────────
def get_lyrics(genius, track):
    if not genius: return None
    try:
        cleaned = clean_title(track["title"])
        song = genius.search_song(cleaned, track["artist"])
        return song.lyrics if song else None
    except: return None

def get_synced(track):
    try:
        import urllib.parse
        artist = urllib.parse.quote(track['artist'])
        title = urllib.parse.quote(track['title'])
        url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={title}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200: return r.json().get("syncedLyrics")
    except: pass
    return None

# ─── PROCESAR CANCIÓN ─────────────────────────────────────
def process_track(genius, track, send=False):
    mp3_path, track_info = download_mp3(track)
    if not mp3_path: return
    
    lyrics = get_lyrics(genius, track)
    synced = get_synced(track)
    embed_tags(mp3_path, track, lyrics, synced)
    
    log.info(f"{track['artist']} - {track['title']} ✓ Completada")
    
    if send:
        send_to_mobile(mp3_path, track['artist'], track['album'])


# ─── MAIN CLI ─────────────────────────────────────────────
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artist", help="Artista")
    parser.add_argument("-t", "--title", help="Título")
    parser.add_argument("--album", default="Unknown Album", help="Álbum")
    parser.add_argument("--send", action="store_true", help="Enviar a móvil")
    args = parser.parse_args()

    genius = None
    if GENIUS_TOKEN:
        genius = lyricsgenius.Genius(GENIUS_TOKEN, timeout=10, verbose=False, remove_section_headers=True)

    if args.artist and args.title:
        track = {"artist": args.artist, "title": args.title, "album": args.album}
        process_track(genius, track, send=args.send)
    else:
        print("Uso: python musicDownloader3.py -a Artist -t Title [--send]")
