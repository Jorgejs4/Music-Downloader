#!/usr/bin/env bash
set -euo pipefail

echo "[Setup] Creando entorno virtual y instalando dependencias..."

VENV_DIR=".venv"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install yt_dlp mutagen lyricsgenius spotipy

echo "[Setup] Creando archivo .env con variables de ejemplo (opcional)" 
if [ ! -f .env ]; then
  cat > .env << 'ENV'
# Exporta estas variables en tu entorno real
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
GENIUS_TOKEN=
ENV
fi

echo "[Setup] Listo. Recuerda no versionar credenciales."
