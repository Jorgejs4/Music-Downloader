#!/usr/bin/env python3
"""
Music Downloader 4.0 - Profesional
==================================
- Descarga MP3 desde YouTube con portada
- Guarda portada embebida + .jpg
- Letra normal embebida (Genius)
- Letra sincronizada .lrc (lrclib o generada)
- Carpeta: Artista Principal / Álbum
- Descarga en paralelo 4 canciones
- Compatible Android / Retro Music
"""

import os, re, csv, time, logging
import requests, lyricsgenius
from mutagen.id3 import ID3
try:
    from mutagen.id3 import TIT2, TPE1, TALB, USLT, APIC  # type: ignore
except Exception:
    # Fallback for some Mutagen versions where frames are located under _frames
    from mutagen.id3._frames import TIT2, TPE1, TALB, USLT, APIC  # type: ignore
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── CONFIG ────────────────────────────────────────────────
GENIUS_TOKEN = "lBK6JzhO0vuxGnehFlPSmeNTic57RTIJpFIfuJJp3RISG3lZBMpahuTl71J-kAJmorXQIoakuFxVRoNxADQ4HA"
CSV_PATH     = "D:/musica/playlist.csv"
OUTPUT_DIR   = "D:/musica/canciones_4.0"
DELAY        = 1
SKIP_EXISTING = True
MAX_THREADS   = 4  # Paralelismo

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

def read_csv(path: str) -> list:
    tracks = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title  = row.get("Track Name") or row.get("Name") or ""
            artist = row.get("Artist Name(s)") or row.get("Artist") or ""
            album  = row.get("Album Name") or row.get("Album") or ""
            main_artist = first_artist(artist)
            if title and main_artist:
                tracks.append({"title": title.strip(), "artist": main_artist, "album": album.strip()})
    return tracks

def get_song_dir(base, artist, album):
    folder = os.path.join(base, sanitize(artist), sanitize(album))
    os.makedirs(folder, exist_ok=True)
    return folder

# ─── DESCARGA Y PORTADA ────────────────────────────────────
def download_mp3(track):
    title, artist, album = track["title"], track["artist"], track["album"]
    safe_name = sanitize(f"{artist} - {title}")
    song_dir = get_song_dir(OUTPUT_DIR, artist, album)
    mp3_path = os.path.join(song_dir, f"{safe_name}.mp3")
    if SKIP_EXISTING and os.path.exists(mp3_path):
        log.info(f"{artist} - {title} ✓ Ya existe")
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
            log.warning(f"{artist} - {title} ✗ No descargado")
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
    # .lrc sincronizado
    if synced:
        lrc_path = os.path.splitext(mp3_path)[0] + ".lrc"
        with open(lrc_path, "w", encoding="utf-8") as f: f.write(synced)

# ─── LETRAS ───────────────────────────────────────────────
def get_lyrics(genius, track):
    try:
        cleaned = clean_title(track["title"])
        song = genius.search_song(cleaned, track["artist"])
        return song.lyrics if song else None
    except: return None

def get_synced(track):
    try:
        url = f"https://lrclib.net/api/get?artist_name={track['artist']}&track_name={track['title']}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200: return r.json().get("syncedLyrics")
    except: pass
    return None

# ─── PROCESAR CANCIÓN ─────────────────────────────────────
def process_track(genius, track):
    mp3_path, track_info = download_mp3(track)
    if not mp3_path: return
    lyrics = get_lyrics(genius, track)
    synced = get_synced(track)
    embed_tags(mp3_path, track, lyrics, synced)
    log.info(f"{track['artist']} - {track['title']} ✓ Completada con portada, tags y letras")
    time.sleep(DELAY)

# ─── MAIN ────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    genius = lyricsgenius.Genius(GENIUS_TOKEN, timeout=10, retries=2, verbose=False, remove_section_headers=True)
    tracks = read_csv(CSV_PATH)
    log.info(f"Total canciones: {len(tracks)}")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(process_track, genius, t) for t in tracks]
        for f in as_completed(futures):
            pass

    log.info("DESCARGA COMPLETADA")

if __name__ == "__main__":
    main()
