# 🎵 Music Downloader (Spotify → YouTube MP3)

Herramienta automatizada para descargar canciones de Spotify con la mejor calidad de YouTube, incluyendo metadatos, portadas y letras sincronizadas (.LRC).

---

## 🚀 Propósito del Proyecto
Este conjunto de scripts permite automatizar el flujo de descarga de música para reproductores locales (como Retro Music en Android).

- **Busca** canciones en YouTube con la máxima fidelidad posible.
- **Descarga** y convierte a MP3 (320kbps recomendado).
- **Etiqueta** con metadatos reales de Spotify (Título, Artista, Álbum, Año).
- **Descarga letras** normales y sincronizadas (LRC) mediante Genius y LRCLib.
- **Sincroniza** mediante ADB a tu dispositivo Android (Próximamente: Flujo directo en Termux).

---

## 📂 Estructura de Archivos
- **`musicDownloader3.py`**: El motor principal. Gestiona las descargas (`yt-dlp`), el etiquetado (`mutagen`) y la obtención de letras.
- **`music_csv_auto.py`**: Procesa listas de reproducción masivas desde un archivo `playlist.csv` (exportado de Spotify).
- **`auto_sync.py`**: Orquestador principal que coordina el robot de Exportify y la descarga.
- **`exportify_bot.py`**: Automatización de navegador para obtener el CSV de tus canciones de Spotify.
- **`downloaded.json`**: Base de datos local para evitar descargas duplicadas.

---

## 🛠️ Próximos Pasos: Migración a Termux
Estamos trabajando en un flujo nativo para **Android (Termux)** para que no necesites un ordenador encendido:
1.  **Eliminar dependencia de ADB**: Guardar directamente en el almacenamiento interno del móvil.
2.  **API de Spotify**: Usar la API oficial para leer tus "Liked Songs" sin necesidad de archivos CSV manuales.
3.  **Ejecución 24/7**: Descargar música en segundo plano desde el móvil.

---

## ⚙️ Configuración (.env)
Asegúrate de tener un archivo `.env` con las siguientes claves:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `GENIUS_ACCESS_TOKEN`
- `OUTPUT_DIR` (Carpeta donde se guardará la música)

---

## 📜 Uso
Para lanzar la sincronización completa en PC:
```powershell
./Lanzar_Sincronizacion.bat
```

Para uso manual:
```bash
python musicDownloader3.py -a "Nombre Artista" -t "Nombre Canción"
```

---
*Mantenido por [Jorgejs4](https://github.com/Jorgejs4)*
