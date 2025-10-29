# 🧪 Guía de Testing - Sin Subir a YouTube

Esta guía te ayudará a probar el sistema completo sin configurar OAuth ni subir videos a YouTube.

## ✅ Checklist de Pre-Test

Antes de empezar, asegúrate de tener:

- [x] Python 3.9+ instalado
- [x] FFmpeg instalado y en PATH
- [x] Dependencias instaladas (`pip install -r requirements.txt`)
- [x] YouTube API Key configurada en `.env`
- [x] Al menos 5GB de espacio libre en disco
- [x] Al menos 4GB de RAM libre

**NO necesitas:**
- ❌ OAuth configurado
- ❌ `client_secrets.json`
- ❌ Canal de YouTube

## 🚀 Método 1: Test Rápido Automático

El método más fácil para probar **ambas funcionalidades**:

```bash
python test_system.py
```

### Opciones del Test:

Al ejecutar, verás un menú:

```
🧪 SYSTEM TEST - Choose Test Mode
======================================================================

1. 🔍 Test TRENDING SEARCH (Find popular songs in Spain)
2. 🎵 Test SPECIFIC URL (Process a specific song)
0. ❌ Exit

Select option:
```

#### Opción 1: Test de Búsqueda de Tendencias 🔍

```bash
Select option: 1
```

**Qué hace:**
1. ✅ Busca las canciones más populares en España HOY
2. ✅ Muestra lista con título, artista, vistas
3. ✅ Te permite seleccionar una para procesar
4. ✅ Procesa y genera el video
5. ❌ NO sube a YouTube

**Ejemplo de salida:**

```
🔍 TESTING TRENDING SEARCH
======================================================================

Searching for trending songs in Spain...
Region: ES
Max results: 10

✅ Found 10 trending songs!

----------------------------------------------------------------------
Top trending songs in Spain:
----------------------------------------------------------------------
 1. [New   ] BZRP Music Sessions #53
     Artist: Bizarrap                           | Views: 234,567,890

 2. [New   ] La Bebe (Remix)
     Artist: Yng Lvcas                          | Views: 123,456,789

 3. [✓ In DB] Shakira || BZRP Music Sessions
     Artist: Bizarrap                           | Views: 456,789,012

...

Which song do you want to process?
Enter number (1-10) or 0 to skip:
Choice: 1

✅ Added to database: BZRP Music Sessions #53
🚀 Processing will now start...
```

#### Opción 2: Test con URL Específica 🎵

```bash
Select option: 2
```

**Qué hace:**
1. ✅ Te pide una URL de YouTube
2. ✅ Descarga el audio
3. ✅ Separa voces/instrumental
4. ✅ Modifica el instrumental
5. ✅ Transcribe las letras
6. ✅ Genera el video de karaoke
7. ✅ Guarda todo en `data/videos/`
8. ❌ NO sube a YouTube

**Ejemplo de uso:**

```bash
🎵 TESTING SPECIFIC URL
======================================================================

Enter a YouTube URL to test (recommend a SHORT song, 2-3 minutes):
Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ

YouTube URL: https://www.youtube.com/watch?v=ABC123

🚀 Processing will now start. This may take several minutes...
```

### Salida esperada (ambas opciones):

```
🎉 TEST SUCCESSFUL!
======================================================================

📁 Files generated:
   Audio: data/downloads/Artist - Song_ABC123.wav
   Vocals: data/processed/ABC123/vocals.wav
   Instrumental: data/processed/ABC123/instrumental.wav
   Modified: data/processed/ABC123/instrumental_modified.wav
   Lyrics: data/processed/ABC123/lyrics.ass
   VIDEO: data/videos/Artist - Song_ABC123.mp4

📹 You can find your karaoke video at:
   data/videos/Artist - Song_ABC123.mp4

✅ System is working correctly!
```

## 🎯 Método 2: Usando el Menú Principal

```bash
python main.py
```

**Ahora tienes DOS formas de probar desde el menú:**

### Opción 1: Buscar Tendencias 🔍

```
🎤 KARAOKE AUTOMATION SYSTEM
======================================================================

1. 🔍 Search for trending songs  ← Selecciona esta para tendencias
2. 🎵 Process a specific YouTube URL
3. 📋 Process pending songs
4. 📊 Show database stats
5. 🗑️  Clear failed songs
0. ❌ Exit

Select option: 1
```

**Qué verás:**

```
🔥 TOP TRENDING SONGS IN SPAIN
======================================================================

 1. [New   ] BZRP Music Sessions #53
     Artist: Bizarrap                           | Views: 234,567,890

 2. [New   ] La Bebe (Remix)
     Artist: Yng Lvcas                          | Views: 123,456,789

 3. [✓ In DB] Shakira || BZRP Music Sessions
     Artist: Bizarrap                           | Views: 456,789,012

...

Options:
  1. Add ALL new songs to database (for batch processing later)
  2. Select ONE song to process now
  0. Cancel

Select option: 2
Which song? (enter number 1-10)
Number: 1

✅ Selected: BZRP Music Sessions #53
🎵 Starting processing...
```

### Opción 2: URL Específica 🎵

```
Select option: 2
```

Ingresa la URL y el sistema procesará sin subir:

```
Enter YouTube URL or video ID: https://www.youtube.com/watch?v=ABC123

✅ Added to database:
  Title: Example Song
  Artist: Example Artist

🎵 Starting processing...
```

## 📊 Verificar Resultados

### Estructura de archivos generados:

```
data/
├── downloads/
│   └── Artist - Song_ABC123.wav         ← Audio original
├── processed/
│   └── ABC123/
│       ├── vocals.wav                   ← Solo voz
│       ├── instrumental.wav             ← Solo instrumental
│       ├── instrumental_modified.wav    ← Instrumental modificado
│       ├── lyrics.srt                   ← Letras con timestamps
│       └── lyrics.ass                   ← Letras estilo karaoke
└── videos/
    └── Artist - Song_ABC123.mp4         ← 🎬 VIDEO FINAL
```

### Reproducir el video:

El video estará en `data/videos/`. Ábrelo con:
- **Windows**: VLC, Windows Media Player
- **Mac**: QuickTime, VLC
- **Linux**: VLC, mpv

### Verificar calidad:

Reproduce el video y verifica:
- ✅ Audio instrumental se escucha bien
- ✅ Letras aparecen sincronizadas
- ✅ Palabras se resaltan correctamente
- ✅ Visualizador de audio se mueve
- ✅ No hay glitches ni cortes

## 🔧 Configuración para Testing

### Configuración Recomendada Inicial

En `config.yaml`:

```yaml
# Audio Processing
audio:
  modification:
    enabled: true  # Puedes desactivar para tests más rápidos
  transcription:
    model: "base"  # tiny = más rápido, base = balance

# Video
video:
  resolution: "1920x1080"  # Puedes bajar a 1280x720 para más velocidad
  fps: 30

# Upload (IMPORTANTE)
upload:
  auto_upload: false  # ← Asegúrate que está en false
```

### Para tests más rápidos:

Si solo quieres probar que funciona (no calidad final):

```yaml
audio:
  modification:
    enabled: false  # Salta modificación
  transcription:
    model: "tiny"   # Modelo más rápido

video:
  resolution: "1280x720"  # Menor resolución
  fps: 24
```

Esto reduce el tiempo de ~10min a ~5min por canción.

## 🎵 Canciones Recomendadas para Testing

### Canciones Cortas (2-3 minutos)

Usa canciones cortas para tests iniciales:
- Menos tiempo de procesamiento
- Menos espacio en disco
- Más rápido para iterar

### Canciones en Español

Para probar la transcripción en español:
- El modelo Whisper funciona mejor con español claro
- Verifica que `language: "es"` en config.yaml

### Evita (para tests iniciales)

- ❌ Canciones muy largas (>5 minutos)
- ❌ Canciones con mucho ruido/distorsión
- ❌ Canciones instrumentales (no hay letras que transcribir)
- ❌ Canciones con idiomas mezclados

## 📝 Logs y Debug

### Ver logs en tiempo real:

Los logs se guardan en `logs/karaoke.log`:

```bash
# Windows PowerShell
Get-Content logs/karaoke.log -Wait

# Linux/Mac
tail -f logs/karaoke.log
```

### Logs importantes a revisar:

```
2025-10-29 12:00:00 | INFO | Downloading audio: <URL>
2025-10-29 12:00:30 | INFO | Audio downloaded: Song.wav (45.2 MB)
2025-10-29 12:01:00 | INFO | Separating vocals and instrumental
2025-10-29 12:03:00 | INFO | Audio separated successfully
2025-10-29 12:03:05 | INFO | Modifying instrumental
2025-10-29 12:04:00 | INFO | Transcribing vocals with Whisper
2025-10-29 12:05:00 | INFO | Lyrics transcribed: 42 segments
2025-10-29 12:05:05 | INFO | Generating ASS karaoke lyrics
2025-10-29 12:05:10 | INFO | Creating karaoke video
2025-10-29 12:08:00 | INFO | Video created successfully (125.4 MB)
2025-10-29 12:08:01 | INFO | ⏭️  YouTube upload DISABLED - Skipping upload
2025-10-29 12:08:01 | INFO | ✅ Successfully processed: Song
```

## 🐛 Problemas Comunes en Testing

### "Spleeter separation failed"

**Causa**: Falta de RAM o modelo no encontrado

**Solución**:
```bash
# Verificar que Spleeter está instalado
pip show spleeter

# Reinstalar si es necesario
pip install spleeter==2.4.0
```

### "Whisper out of memory"

**Causa**: Modelo muy grande para tu RAM/VRAM

**Solución**: Usa modelo más pequeño en config.yaml:
```yaml
audio:
  transcription:
    model: "tiny"  # o "base"
```

### "FFmpeg not found"

**Solución**:
```bash
# Verificar instalación
ffmpeg -version

# Si no está, instalar y añadir a PATH
```

### Video sin letras

**Causa**: Problema en la generación del .ass o en FFmpeg

**Solución**:
1. Verifica que `lyrics.ass` existe en `data/processed/<ID>/`
2. Revisa logs para errores en la generación de ASS
3. Verifica que FFmpeg soporta subtitles: `ffmpeg -filters | grep ass`

## ✅ Criterios de Éxito

Un test exitoso debe:

- [x] Descargar audio completo
- [x] Separar voces e instrumental (2 archivos .wav)
- [x] Modificar instrumental si está habilitado
- [x] Transcribir letras (archivo .srt con timestamps)
- [x] Generar letras ASS con estilos
- [x] Crear video MP4 con todo integrado
- [x] NO intentar subir a YouTube
- [x] Video reproducible sin errores

## 🔄 Iterar y Mejorar

Una vez que el test básico funciona:

1. **Ajusta estilos de letras** en `config.yaml`
2. **Prueba diferentes colores** para el visualizador
3. **Añade fondos personalizados** en `data/backgrounds/`
4. **Experimenta con modificaciones** de audio
5. **Prueba diferentes modelos** de Whisper (tiny → base → small)

Cada cambio se puede probar sin subir nada, solo procesando de nuevo.

## 📤 Cuando estés listo para subir

Solo cuando todo funcione perfectamente:

1. Configura OAuth (ver `YOUTUBE_API_SETUP.md`)
2. Cambia `auto_upload: true` en `config.yaml`
3. Procesa una canción de prueba
4. Verifica en YouTube que se subió correctamente
5. Ajusta metadata (título, descripción, tags) si es necesario

## 💡 Tips para Testing Eficiente

- **Usa siempre la misma canción corta** para comparar cambios
- **Guarda configuraciones diferentes** (config_fast.yaml, config_hq.yaml)
- **Documenta qué funciona** y qué no
- **Prueba incrementalmente**: primero audio, luego video, luego estilos
- **No borres archivos intermedios** hasta verificar el resultado final

---

¿Preguntas sobre testing? Consulta `README.md` o abre un [issue](https://github.com/miguel17693/ytb-automate/issues) 🧪
