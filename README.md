# 🎵 Music Downloader (Spotify → YouTube MP3) v4.0

Herramienta automatizada para descargar canciones de Spotify con la mejor calidad de YouTube (320kbps), incluyendo metadatos ID3v2.3, portadas y letras sincronizadas (.LRC).

---

## 🚀 Propósito del Proyecto
Este ecosistema permite automatizar el flujo completo de descarga y etiquetado para reproductores locales (como Retro Music en Android).

- **Busca** canciones en YouTube con la máxima fidelidad posible (prioriza audios oficiales).
- **Descarga** y convierte a MP3 con 320kbps CBR.
- **Etiqueta** con metadatos de Spotify (Título, Artista, Álbum, Año).
- **Letras Sincronizadas**: Descarga archivos `.lrc` mediante **LRCLib** y letras normales (`USLT`) mediante **Genius**.
- **Base de Datos**: Usa `downloaded.json` para evitar descargar duplicados.
- **Entorno Híbrido**: Detección inteligente de entorno (PC vs Termux) para guardar archivos localmente o enviarlos vía ADB.

---

## 📂 Estructura de Archivos (Core)
- **`musicDownloader3.py`**: El motor principal v4.0. Gestiona descargas (`yt-dlp`), etiquetado (`mutagen`) y letras.
- **`music_csv_auto.py`**: Procesa `playlist.csv` (exportado de Spotify), gestiona la base de datos y la organización de carpetas.
- **`auto_sync.py`**: Orquestador principal que coordina el bot de Exportify y la descarga.
- **`exportify_bot.py`**: Automatización con Playwright para extraer tus "Liked Songs" de Spotify.
- **`spotify_sync.py`**: Alternativa "Ghost Mode" que sincroniza vía scraping web sin necesidad de CSV.

---

## 📱 Solución Termux (Pantalla Apagada)
Si usas Termux y el script se detiene al apagar la pantalla, Android está matando el proceso por ahorro de energía.

### 1. Activar Wake Lock
Ejecuta el siguiente comando en Termux antes de lanzar el script:
```bash
termux-wake-lock
```
Esto evita que la CPU entre en modo de suspensión (CPU sleep).

### 2. Configuración de Android
- Ve a **Ajustes > Aplicaciones > Termux**.
- En **Batería**, selecciona **Sin restricciones** (u "Optimizar uso de batería" -> "No optimizar").
- Asegúrate de que Termux tenga el permiso de "Ejecución en segundo plano".

---

## ⚙️ Configuración (.env)
Asegúrate de tener un archivo `.env` (basado en `.env.template`) con:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `GENIUS_ACCESS_TOKEN`
- `OUTPUT_DIR` (Donde se guardará la música, ej: `/sdcard/Music/` en Termux)

---

## 📜 Uso
Para lanzar la sincronización completa en PC:
```powershell
./Lanzar_Sincronizacion.bat
```

Para uso manual en Termux/PC:
```bash
python musicDownloader3.py -a "Nombre Artista" -t "Nombre Canción"
```

---
*Mantenido por [Jorgejs4](https://github.com/Jorgejs4) - v4.0 Marzo 2026*
