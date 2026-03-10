Music Downloader – Configuración, seguridad y pruebas
===================================================

Este proyecto automatiza la descarga de playlists de Spotify y descarga música desde YouTube (incluyendo portada y letras cuando es posible). También permite enviar archivos al móvil vía ADB. A continuación se detallan los cambios de seguridad, cómo configurarlo con variables de entorno y un plan de pruebas para validar cada parte.

Notas importantes sobre seguridad
- No se deben subir credenciales al repositorio. Las credenciales deben leerse desde variables de entorno o archivos de configuración no versionados (p. ej. .env).
- Este repositorio ya contenía credenciales sensibles en el historial. He preparado herramientas y pasos para eliminar esas credenciales de la historia y evitar exponer secretos en el futuro.

Estructura relevante
- musicDownloader3.py: descargador desde YouTube, añade portada y metadatos; soporta uso por CSV o descarga puntual vía CLI.
- music_auto.py: sincroniza tu librería de Spotify con lo descargado, invoca musicDownloader3.py para cada canción nueva y gestiona el historial de descargas.
- playlist.csv: CSV de ejemplo con pistas (no se debe depender de credenciales en este archivo para la ejecución segura).
- scripts/: utilidades para configurar el entorno y purgar credenciales de la historia.
- .env.template: ejemplo de variables de entorno para configuración segura.
- README.md: este archivo (docs de configuración y pruebas).

Configuración rápida (entorno local)
- Requisitos: Python 3.x, pip, adb (opcional para envío móvil).
- Variables de entorno (recomendado): SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, GENIUS_TOKEN.
- CSV: playlist.csv debe ubicarse en la ruta indicada por CSV_PATH o en el mismo directorio del script.

Archivos de configuración y helpers
- .env.template: archivo de ejemplo para definir variables de entorno localmente.
- scripts/setup_env.sh: script para entornos Unix-like (Linux/macOS).
- scripts/setup_env.ps1: script para Windows.
- scripts/purge_credentials_history.sh: purga automática de credenciales de la historia (requiere git-filter-repo).
- scripts/strip_secrets.txt: reglas de sustitución para eliminar secretos de la historia (usadas por purge script).

Plan de pruebas y validación
1) Configuración de entorno
- Define las variables de entorno necesarias en un archivo .env o en el entorno del sistema.
- Verifica que python, pip, yt_dlp, mutagen, lyricsgenius, spotipy y adb estén disponibles.

2) Prueba de descarga individual
- Ejecuta: python musicDownloader3.py -a "Artist" -t "Song" --csv playlist.csv --output canciones
- Verifica que se cree el MP3, se embedan portada y metadata, y que exista el archivo .mp3 en la ruta de salida.

3) Prueba de descarga por CSV
- Coloca playlist.csv en la ruta especificada o usa la ruta de CSV indicada por --csv.
- Ejecuta: python musicDownloader3.py --csv playlist.csv --output canciones
- Revisa que se generen las carpetas por artista/álbum y que cada pista tenga su MP3 y portada.

4) Letras y sincronización
- Si GENIUS_TOKEN está definido, verifica que las letras se añadan en USLT y que se guarde un .lrc si se obtiene sincronización.
- Si no hay GENIUS_TOKEN, las letras deben omitirse sin fallar.

5) Envío a móvil (opcional)
- Conecta un dispositivo Android y asegúrate de que adb funcione.
- Ejecuta: python musicDownloader3.py --csv playlist.csv --output canciones --send
- Verifica que el archivo MP3 se copie en /sdcard/Music del móvil (o ruta configurable).

6) Limpieza de historial de secretos (opcional, historial de git)
- Ejecuta scripts/purge_credentials_history.sh para purgar credenciales de la historia (requiere git-filter-repo).
- Después de purgar, crea un PR para incorporar cambios a master si procede.

Notas finales y siguientes pasos
- Mantener credenciales fuera del código fuente y del historial de la repo.
- Añadir pruebas automatizadas si se desea un CI sencillo (p. ej. pytest con mocks para calls a YouTube y a Spotify).
- Si quieres, puedo ayudarte a crear un flujo de CI para validar descargas y generación de metadatos sin descargar archivos grandes.

- Proximos pasos propuestos:
- 1) Ejecutar purga segura de historial y confirmar que no quedan secretos en el repositorio.
- 2) Mantener un archivo .env.template y scripts de setup para facilitar la instalación.
- 3) Añadir pruebas básicas para parseo de CSV y generación de rutas de salida.

Archivo de ejemplo y plantillas
- .env.template: contiene ejemplos de variables de entorno y descripciones.
- scripts/strip_secrets.txt: reglas de sustitución para eliminar secretos en la historia.
- scripts/setup_env.sh / scripts/setup_env.ps1: herramientas de setup para Windows y Linux.

Notas de formato de código y convenciones
- Se intenta mantener las dependencias y rutas lo más portables posible, usando rutas relativas y variables de entorno.
- Si la ruta de salida o CSV cambia, utiliza las variables de entorno o pasa argumentos de CLI para que no haya hardcodes.

Contacto y ayuda
- Si necesitas ayuda para adaptar a un entorno específico, dime qué sistema operativo utilizas y si quieres un flujo de despliegue en un servidor o PC local.
