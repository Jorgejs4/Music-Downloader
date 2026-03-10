<# Setup script for Windows PowerShell #>
Write-Host "Setup environment for Music Downloader"
$venv = ".\.venv"
if (Test-Path $venv) { Remove-Item -Recurse -Force $venv }
python -m venv $venv
& $venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install yt_dlp mutagen lyricsgenius spotipy

if (-Not (Test-Path ".env")) {
@"
# SPOTIFY_CLIENT_ID=...
# SPOTIFY_CLIENT_SECRET=...
# SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
# GENIUS_TOKEN=...
"@ | Out-File -Encoding ascii .env
}

Write-Host "Setup complete. Do not commit credentials."
